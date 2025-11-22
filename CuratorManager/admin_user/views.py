import os.path
from builtins import print
from django.http import HttpResponse
from django.conf import settings
from django.db import connection, transaction
from django.shortcuts import render,redirect
from django.contrib import messages
from reportlab.pdfgen import canvas
from openpyxl import Workbook
import io
from admin_user.forms.GroundMasterForm import GroundMasterForm
from admin_user.forms.PitchMasterForm import PitchMasterForm
from admin_user.forms.adminRoleForm import AdminUserRoleForm
from admin_user.forms.StateCityForm import StateCityForm
from admin_user.models import AdminRole
from super_admin_user.models import AdminUserList


from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import csv
from xhtml2pdf import pisa
from django.template.loader import get_template
from datetime import datetime

#######################reports

def reportMatch(request):
    return render(request,'admin_user/reports/report1.html',{"records":"none"})


def fetch_tournaments(request):
    org_id = request.session.get('org_id')
    match_type = request.GET.get("match_type")
    season_year = request.GET.get("season_year")
    if(match_type!="Multidays"):
        query = f"""
        SELECT DISTINCT name_tournament
        FROM {org_id}_match_master
        WHERE match_type = %s AND (YEAR(match_date) = %s OR YEAR(match_date) = %s)
    """
    else:
        query = f"""
        SELECT DISTINCT name_tournament
        FROM {org_id}_match_master
        WHERE match_type = %s AND (YEAR(from_date) = %s OR YEAR(from_date) = %s)
    """

    with connection.cursor() as cursor:
        cursor.execute(query, [match_type, season_year,int(season_year)+1])
        data = [row[0] for row in cursor.fetchall()]

    return JsonResponse({"tournaments": data})


def fetch_cities(request):
    org_id = request.session.get('org_id')
    tournament = request.GET.get("name_tournament")
    query = f"""
        SELECT DISTINCT vgm.city_name
        FROM {org_id}_match_master vmm
        JOIN {org_id}_ground_master vgm ON vmm.ground_id = vgm.id
        WHERE vmm.name_tournament = %s
    """

    with connection.cursor() as cursor:
        cursor.execute(query, [tournament])
        data = [row[0] for row in cursor.fetchall()]

    return JsonResponse({"cities": data})


def fetch_grounds(request):
    org_id = request.session.get('org_id')
    tournament = request.GET.get("name_tournament")
    city = request.GET.get("city_name")
    
    query = f"""
        SELECT DISTINCT vgm.id, vgm.ground_name
        FROM {org_id}_match_master vmm
        JOIN {org_id}_ground_master vgm ON vmm.ground_id = vgm.id
        WHERE vmm.name_tournament = %s AND vgm.city_name = %s
    """

    with connection.cursor() as cursor:
        cursor.execute(query, [tournament, city])
        data = cursor.fetchall()
        print(data)

    grounds = [{"id": g[0], "name": g[1]} for g in data]
    return JsonResponse({"grounds": grounds})


def fetch_matches(request):
    org_id = request.session.get('org_id')
    ground_id = request.GET.get("ground_id")
    tournament = request.GET.get("name_tournament")
    query = f"""
        SELECT id, team1, team2, match_date,from_date,to_date,match_type
        FROM {org_id}_match_master
        WHERE ground_id = %s AND name_tournament = %s
    """

    with connection.cursor() as cursor:
        cursor.execute(query, [ground_id, tournament])
        data = cursor.fetchall()

    matches = []
    for m in data:
        if(m[6]=="Multidays"):
            formatted_date = m[4]+" to "+m[5]
        else:
            formatted_date = m[3].strftime("%d-%m-%Y") if isinstance(m[3], datetime) else m[3]
            
            
        matches.append({
            "id": m[0],
            "label": f"{m[1]} vs {m[2]} ({formatted_date})"
        })

    return JsonResponse({"matches": matches})


def fetch_match_report(request):
    org_id = request.session.get('org_id')
    match_id = request.GET.get("match_id")
    query = f"""
        SELECT * FROM {org_id}_match_master WHERE id = %s
    """

    with connection.cursor() as cursor:
        cursor.execute(query, [match_id])
        columns = [col[0] for col in cursor.description]
        data = cursor.fetchone()
        record = dict(zip(columns, data)) if data else {}

    return render(request, "admin_user/reports/match_report_result.html", {"record": record})


def fetch_match_records(request):
    org_id = request.session.get('org_id')
    match_id = request.GET.get("match_id")
    team1 = request.GET.get("team1")
    team2 = request.GET.get("team2")
    match_date = request.GET.get("match_date")
    match_type = request.GET.get("match_type")
    name_tournament = request.GET.get("name_tournament")
    print(match_type)
    filters = []
    params = []

    if match_id:
        filters.append("vmm.id = %s")
        params.append(match_id)
    else:
        if match_type:
            
            filters.append("vmm.match_type = %s")
            params.append(f"{match_type}")

        if team1:
            filters.append("vmm.team1 LIKE %s")
            params.append(f"{team1}")

        if team2:
            filters.append("vmm.team2 LIKE %s")
            params.append(f"{team2}")

        if match_date:
            filters.append("vmm.match_date = %s")
            params.append(match_date)

        if name_tournament:
            filters.append("vmm.name_tournament LIKE %s")
            params.append(f"{name_tournament}")

    where_clause = " AND ".join(filters)
    
    if where_clause:
        where_clause = "WHERE " + where_clause
    print(where_clause)

    query = f"""
        SELECT 
          vmm.id AS match_id, vmm.match_type, vmm.name_tournament, vmm.match_date,
          vmm.team1, vmm.team2,vmm.preparation_date,
          vmm.from_date, vmm.to_date,vmm.nuteral_curator,
			`vmm`.`days_count`,
			`vmm`.`start_time`,
			`vmm`.`is_pitch_level`,
			`vmm`.`lawn_height`,
			`vmm`.`grass_cover`,
			`vmm`.`min_temp`,
			`vmm`.`max_temp`,
			`vmm`.`forecast`,
			`vmm`.`moisture_upto`,
			`vmm`.`dew_factor`,
			`vmm`.`access_bounce`,
			`vmm`.`machinery_id`,
			`vmm`.`no_of_passes`,
			`vmm`.`rolling_speed`,
			`vmm`.`last_watering_on`,
			`vmm`.`quantity_of_water`,
			`vmm`.`time_of_application`,
			`vmm`.`time_roller`,
			`vmm`.`is_daily_watering`,
			`vmm`.`mover_machinery_id`,
			`vmm`.`date_mowing_done_last`,
			`vmm`.`time_of_application_mover`,
			`vmm`.`mowing_done_at_mm`,
			`vmm`.`is_fertilizers_used`,
			`vmm`.`fertilizers_details`,
			`vmm`.`chemical_details_remark`,
			`vmm`.`remark_by_groundsman`,
			`vmm`.`out_machinery_id`,
			`vmm`.`out_no_of_passes`,
			`vmm`.`out_rolling_speed`,
			`vmm`.`out_last_watering_on`,
			`vmm`.`out_quantity_of_water`,
			`vmm`.`out_time_of_application`,
			`vmm`.`out_time_roller`,
			`vmm`.`out_is_daily_watering`,
			`vmm`.`out_mover_machinery_id`,
			`vmm`.`out_date_mowing_done_last`,
			`vmm`.`time_of_application_out_mover`,
			`vmm`.`out_mowing_done_at_mm`,
			`vmm`.`out_is_fertilizers_used`,
			`vmm`.`out_fertilizers_details`,
			`vmm`.`out_chemical_details_remark`,
			`vmm`.`out_remark_by_groundsman`,
			`vmm`.`brief_match_pitch_assessment`,
			`vmm`.`time_of_application_chemical`,
			`vmm`.`out_time_of_application_chemical`,
			`vmm`.`created_at`,
			`vmm`.`updated_at`,
			`vmm`.`chemical_weight`,
			`vmm`.`fertilizers_unit`,
			`vmm`.`out_chemical_weight`,
			`vmm`.`out_fertilizers_unit`,
			`vmm`.`nuteral_curator`,
			`vmm`.`out_mover_machine_type`,
			`vmm`.`out_mover_machinery_name_operator`,
			`vmm`.`out_moving_passes_unit`,
			`vmm`.`out_mowing_duration`,
			`vmm`.`mover_machine_type`,
			`vmm`.`mover_machinery_name_operator`,
			`vmm`.`moving_passes_unit`,
			`vmm`.`mowing_duration`,
			`vmm`.`roller_machine_type`,
			`vmm`.`roller_machinery_name_operator`,
			`vmm`.`out_roller_machine_type`,
			`vmm`.`out_roller_machinery_name_operator`,
			`vmm`.`passes_unit`,
			`vmm`.`out_passes_unit`,
			`vmm`.`rolling_date`,
			`vmm`.`out_rolling_date`,
          
          vgm.ground_name, vgm.city_name, vgm.state_name, vgm.org_id, vgm.count_main_pitches,
          vgm.count_practice_pitches,
          
          vpm.pitch_no,vpm.id, vpm.pitch_type, vpm.profile_of_pitches,
          vpm.soil_type, vpm.is_uniformtiy_of_grass, vpm.mowing_size, vpm.pitch_placement,
          
        
          
      
          
          sau.id AS admin_id,sau.address AS admin_address,sau.name AS admin_name, 
          sau.email AS admin_email,sau.username AS admin_username, sau.mobile AS admin_mobile
          
        FROM {org_id}_match_master vmm
        LEFT JOIN {org_id}_ground_master vgm ON vmm.ground_id = vgm.id
        LEFT JOIN super_admin_user_adminuserlist sau ON vgm.org_id = sau.org_id
        LEFT JOIN {org_id}_pitch_master vpm ON vmm.pitch_id = vpm.id
       
        {where_clause}
    """
    print(query,params)
    
    
    request.session['match-report-query'] = query
    
    with connection.cursor() as cursor:
        cursor.execute(query, params)
        columns = [col[0] for col in cursor.description]
        rows = cursor.fetchall()
        
        data = [dict(zip(columns, row)) for row in rows]
        print(data)

    return render(request, "admin_user/reports/report1.html", {"records": data})


def download_pdf(request):
    org_id = request.session.get('org_id')
    match_id = request.GET.get("match_id")
    team1 = request.GET.get("team1")
    team2 = request.GET.get("team2")
    match_date = request.GET.get("match_date")
    name_tournament = request.GET.get("name_tournament")

    filters = []
    params = []

    if match_id:
        filters.append("vmm.id = %s")
        params.append(match_id)

    if team1:
        filters.append("vmm.team1 LIKE %s")
        params.append(f"%{team1}%")

    if team2:
        filters.append("vmm.team2 LIKE %s")
        params.append(f"%{team2}%")

    if match_date:
        filters.append("vmm.match_date = %s")
        params.append(match_date)

    if name_tournament:
        filters.append("vmm.name_tournament LIKE %s")
        params.append(f"%{name_tournament}%")

    where_clause = " AND ".join(filters)
    if where_clause:
        where_clause = "WHERE " + where_clause

    query = f"""
        SELECT 
          vmm.id AS match_id, vmm.match_type, vmm.name_tournament, vmm.match_date,
          vmm.team1, vmm.team2,
          vgm.ground_name, vgm.city_name, vgm.state_name, vgm.org_id,
          vpm.pitch_no, vpm.pitch_type, vpm.soil_type,
          vm1.equipment_name AS machinery_name,
          vm2.equipment_name AS mover_machinery_name,
          vm3.equipment_name AS out_machinery_name,
          vm4.equipment_name AS out_mover_machinery_name,
          vfm1.chemical_name AS fertilizers_chemical_name,
          vfm2.chemical_name AS out_fertilizers_chemical_name,
          sau.name AS admin_name, sau.email AS admin_email,
          sau.username AS admin_username, sau.mobile AS admin_mobile
        FROM {org_id}_match_master vmm
        LEFT JOIN {org_id}_ground_master vgm ON vmm.ground_id = vgm.id
        LEFT JOIN super_admin_user_adminuserlist sau ON vgm.org_id = sau.org_id
        LEFT JOIN {org_id}_pitch_master vpm ON vmm.pitch_id = vpm.id
        LEFT JOIN {org_id}_machinery_master vm1 ON vmm.machinery_id = vm1.id
        LEFT JOIN {org_id}_machinery_master vm2 ON vmm.mover_machinery_id = vm2.id
        LEFT JOIN {org_id}_machinery_master vm3 ON vmm.out_machinery_id = vm3.id
        LEFT JOIN {org_id}_machinery_master vm4 ON vmm.out_mover_machinery_id = vm4.id
        LEFT JOIN {org_id}_fertilizer_master vfm1 ON vmm.fertilizers_details = vfm1.id
        LEFT JOIN {org_id}_fertilizer_master vfm2 ON vmm.out_fertilizers_details = vfm2.id
        {where_clause}
    """
    with connection.cursor() as cursor:
        cursor.execute(query, params)
        columns = [col[0] for col in cursor.description]
        data = [dict(zip(columns, row)) for row in cursor.fetchall()]

    template = get_template("admin_user/reports/match_records_pdf.html")
    html = template.render({"records": data})

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = "attachment; filename=match_records.pdf"
    pisa.CreatePDF(html, dest=response)

    return response


def download_csv(request):
    org_id = request.session.get('org_id')
    match_id = request.GET.get("match_id")
    team1 = request.GET.get("team1")
    team2 = request.GET.get("team2")
    match_date = request.GET.get("match_date")
    name_tournament = request.GET.get("name_tournament")

    filters = []
    params = []

    if match_id:
        filters.append("vmm.id = %s")
        params.append(match_id)

    if team1:
        filters.append("vmm.team1 LIKE %s")
        params.append(f"%{team1}%")

    if team2:
        filters.append("vmm.team2 LIKE %s")
        params.append(f"%{team2}%")

    if match_date:
        filters.append("vmm.match_date = %s")
        params.append(match_date)

    if name_tournament:
        filters.append("vmm.name_tournament LIKE %s")
        params.append(f"%{name_tournament}%")

    where_clause = " AND ".join(filters)
    if where_clause:
        where_clause = "WHERE " + where_clause

    query = f"""
        SELECT 
          vmm.id AS match_id, vmm.match_type, vmm.name_tournament, vmm.match_date,
          vmm.team1, vmm.team2,
          vgm.ground_name, vgm.city_name, vgm.state_name, vgm.org_id,
          vpm.pitch_no, vpm.pitch_type, vpm.soil_type,
          vm1.equipment_name AS machinery_name,
          vm2.equipment_name AS mover_machinery_name,
          vm3.equipment_name AS out_machinery_name,
          vm4.equipment_name AS out_mover_machinery_name,
          vfm1.chemical_name AS fertilizers_chemical_name,
          vfm2.chemical_name AS out_fertilizers_chemical_name,
          sau.id AS admin_id, sau.name AS admin_name, sau.email AS admin_email,
          sau.username AS admin_username, sau.mobile AS admin_mobile, sau.address AS admin_address
        FROM {org_id}_match_master vmm
        LEFT JOIN {org_id}_ground_master vgm ON vmm.ground_id = vgm.id
        LEFT JOIN super_admin_user_adminuserlist sau ON vgm.org_id = sau.org_id
        LEFT JOIN {org_id}_pitch_master vpm ON vmm.pitch_id = vpm.id
        LEFT JOIN {org_id}_machinery_master vm1 ON vmm.machinery_id = vm1.id
        LEFT JOIN {org_id}_machinery_master vm2 ON vmm.mover_machinery_id = vm2.id
        LEFT JOIN {org_id}_machinery_master vm3 ON vmm.out_machinery_id = vm3.id
        LEFT JOIN {org_id}_machinery_master vm4 ON vmm.out_mover_machinery_id = vm4.id
        LEFT JOIN {org_id}_fertilizer_master vfm1 ON vmm.fertilizers_details = vfm1.id
        LEFT JOIN {org_id}_fertilizer_master vfm2 ON vmm.out_fertilizers_details = vfm2.id
        {where_clause}
    """

    with connection.cursor() as cursor:
        cursor.execute(query, params)
        columns = [col[0] for col in cursor.description]
        data = cursor.fetchall()

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="match_records.csv"'

    writer = csv.writer(response)

    if data:
        # Step 1: Admin Info
        first_row = dict(zip(columns, data[0]))
        writer.writerow(['Admin Information'])
        writer.writerow(['Admin ID:', first_row.get('admin_id', '')])
        writer.writerow(['Admin Name:', first_row.get('admin_name', '')])
        writer.writerow(['Admin Email:', first_row.get('admin_email', '')])
        writer.writerow(['Admin Username:', first_row.get('admin_username', '')])
        writer.writerow(['Admin Mobile:', first_row.get('admin_mobile', '')])
        writer.writerow(['Admin Address:', first_row.get('admin_address', '')])
        writer.writerow([])  # empty row

        # Step 2: Match Records Table
        # Exclude admin columns from match data
        match_columns = [col for col in columns if not col.startswith("admin_")]
        writer.writerow(match_columns)

        for row in data:
            row_dict = dict(zip(columns, row))
            writer.writerow([row_dict.get(col, '') for col in match_columns])
    else:
        writer.writerow(['No data found'])

    return response


def daily_download_csv(request):
    org_id = request.session.get('org_id')
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')

    filters = []
    params = []

    if from_date and to_date:
        filters.append("rolling_start_date BETWEEN %s AND %s")
        params.extend([from_date, to_date])

    where_clause = " AND ".join(filters)
    if where_clause:
        where_clause = "WHERE " + where_clause

    query = f"""
        SELECT *
        FROM {org_id}_curator_daily_recording_master
        {where_clause}
        ORDER BY rolling_start_date DESC
    """
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="match_records.csv"'

    with connection.cursor() as cursor:
        cursor.execute(query, params)  # Paste same query
        columns = [col[0] for col in cursor.description]
        data = cursor.fetchall()

    writer = csv.writer(response)
    writer.writerow(columns)
    for row in data:
        writer.writerow(row)

    return response


def match_download_csv(request):
    org_id = request.session.get('org_id')
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')

    filters = []
    params = []

    if from_date and to_date:
        filters.append("match_date BETWEEN %s AND %s")
        params.extend([from_date, to_date])

    where_clause = " AND ".join(filters)
    if where_clause:
        where_clause = "WHERE " + where_clause

    query = f"""
        SELECT *
        FROM {org_id}_match_master
        {where_clause}
        ORDER BY match_date DESC
    """

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="match_records.csv"'

    with connection.cursor() as cursor:
        cursor.execute(query, params)  # Paste same query
        columns = [col[0] for col in cursor.description]
        data = cursor.fetchall()

    writer = csv.writer(response)
    writer.writerow(columns)
    for row in data:
        writer.writerow(row)

    return response

def curator_recording_report_page(request):
    return render(request,"admin_user/reports/curator_records_report.html",{"records": "none"})

def curator_recording_report(request):
    org_id = request.session.get('org_id')
    ground_id = request.GET.get("id")
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')

    filters = []
    params = []

    if ground_id:
        filters.append("ground_id = %s")
        params.append(ground_id)

    if from_date and to_date:
        filters.append("rolling_start_date BETWEEN %s AND %s")
        params.extend([from_date, to_date])

    where_clause = " AND ".join(filters)
    if where_clause:
        where_clause = "WHERE " + where_clause

    query = f"""
        SELECT *
        FROM {org_id}_curator_daily_recording_master
        {where_clause}
        ORDER BY rolling_start_date DESC
    """

    with connection.cursor() as cursor:
        cursor.execute(query, params)
        columns = [col[0] for col in cursor.description]
        data = [dict(zip(columns, row)) for row in cursor.fetchall()]

    default_fields = ['id', 'pitch_id', 'pitch_location', 'rolling_start_date', 'min_temp', 'max_temp', 'match_date']
    
    return render(
        request,
        "admin_user/reports/curator_records_report.html",
        {"records": data, 'default_fields': default_fields}
    )


def match_report_page(request):
    return render(request, 'admin_user/reports/match_report.html',{"records": "none"})
    

def match_report(request):
    org_id = request.session.get('org_id')
    ground_id=request.GET.get("id")
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')

    filters = []
    params = []
    if ground_id:
        filters.append("ground_id = %s")
        params.append(ground_id)
        
    if from_date and to_date:
        filters.append("(match_date BETWEEN %s AND %s OR from_date BETWEEN %s AND %s OR to_date BETWEEN %s AND %s)")
        params.extend([from_date, to_date, from_date, to_date, from_date, to_date])


    where_clause = " AND ".join(filters)
    if where_clause:
        where_clause = "WHERE " + where_clause

    query = f"""
        SELECT *
        FROM {org_id}_match_master
        {where_clause}
        ORDER BY match_date DESC
    """

    with connection.cursor() as cursor:
        cursor.execute(query, params)
        columns = [col[0] for col in cursor.description]
        data = [dict(zip(columns, row)) for row in cursor.fetchall()]

    default_fields = ['id', 'match_type', 'name_tournament', 'team1', 'team2', 'preparation_date', 'match_date']
    return render(request, 'admin_user/reports/match_report.html', {'records': data, 'default_fields': default_fields})

def chemicalsReport(request):
      return render(request, "admin_user/reports/ChemicalsReport.html")


def fertilizer_usage_report(request):
    org_id = request.session.get('org_id')
    ground_id = request.GET.get("ground_id")
    from_date = request.GET.get("from_date")
    to_date = request.GET.get("to_date")
    chemical = request.GET.get("chemical").strip()
    print(type(chemical))

    if not all([ground_id, from_date, to_date]):
        return render(request, "admin_user/reports/curator_fertilizer_report.html", {"error": "Please provide all filters."})

    # 1. Fetch fertilizer ID to chemical name mapping
    with connection.cursor() as cursor:
        cursor.execute(f"SELECT id, chemical_name FROM {org_id}_fertilizer_master")
        fert_map = {str(row[0]): row[1] for row in cursor.fetchall()}

    query=""
    value=[]
    if chemical=="" or chemical=="all":
        
    # 2. Fetch relevant fertilizer usage data from curator table
        query = f"""
            SELECT 
                fertilizers_details, pitch_main_chemical_weight, pitch_main_chemical_unit,
                out_fertilizers_details, outfield_chemical_weight, outfield_chemical_unit,
                practice_fertilizers_details, pitch_practice_chemical_weight, pitch_practice_chemical_unit,
                pp_fertilizers_details, practice_area_chemical_weight, practice_area_chemical_unit
            FROM {org_id}_curator_daily_recording_master
            WHERE ground_id = %s AND rolling_start_date BETWEEN %s AND %s
        """
        value.extend([ground_id, from_date, to_date])
    else:
        query = f"""
            SELECT 
                fertilizers_details, pitch_main_chemical_weight, pitch_main_chemical_unit,
                out_fertilizers_details, outfield_chemical_weight, outfield_chemical_unit,
                practice_fertilizers_details, pitch_practice_chemical_weight, pitch_practice_chemical_unit,
                pp_fertilizers_details, practice_area_chemical_weight, practice_area_chemical_unit
            FROM {org_id}_curator_daily_recording_master
            WHERE ground_id = %s AND rolling_start_date BETWEEN %s AND %s 
        """
        value.extend([ground_id, from_date, to_date])
    
    print(query,value)

    with connection.cursor() as cursor:
        cursor.execute(query, value)
        rows = cursor.fetchall()

    usage = {}
    
    usageList=[]
    
    def split_Data(fertilizer_ids_string, weight, unit):
        ids = fertilizer_ids_string.split("__####__")
        weight = weight.split("__####__")
        unit = unit.split("__####__")
        
        min_len = min(len(ids), len(weight), len(unit))
        if(chemical):
            for i in range(min_len):
                f_id = ids[i].strip("_#").strip()
                f_weight = weight[i].strip("_#").strip()
                f_unit = unit[i].strip("_#").strip()

                # âœ… Blank skip karne ke liye condition
                if f_id or f_weight or f_unit:
                    if(f_id==chemical):
                        usageList.append({
                            "id": f_id,
                            "weight": f_weight,
                            "unit": f_unit
                        })
        else:
            for i in range(min_len):
                f_id = ids[i].strip("_#").strip()
                f_weight = weight[i].strip("_#").strip()
                f_unit = unit[i].strip("_#").strip()

                # âœ… Blank skip karne ke liye condition
                if f_id or f_weight or f_unit:
                    usageList.append({
                            "id": f_id,
                            "weight": f_weight,
                            "unit": f_unit
                        })
            



    def add_usage(fertilizer_ids_string, weight, unit):
        
        if not fertilizer_ids_string or not weight or not unit:
            return

        
        try:
            weight = float(weight)
        except:
            return

        unit = unit.strip().lower()

        # Split multiple fertilizer IDs if needed
        fertilizer_ids = [f.strip() for f in fertilizer_ids_string.split(",") if f.strip().isdigit()]

        for fert_id in fertilizer_ids:
            chem_name = fert_map.get(fert_id)
            if not chem_name:
                continue
            usage.setdefault(chem_name, {"kg": 0.0, "ltr": 0.0})
            if unit == "kg":
                usage[chem_name]["kg"] += weight
            elif unit == "gm":
                usage[chem_name]["kg"] += weight / 1000
            elif unit == "ltr":
                usage[chem_name]["ltr"] += weight
            elif unit == "ml":
                usage[chem_name]["ltr"] += weight / 1000
    
    for row in rows:
        split_Data(row[0], row[1], row[2])   # main pitch
        split_Data(row[3], row[4], row[5])   # outfield
        split_Data(row[6], row[7], row[8])   # practice
        split_Data(row[9], row[10], row[11]) # practice area
    
    print(usageList)
    for row in usageList:
        add_usage(row.get("id"), row.get("weight"), row.get("unit"))   # main pitch
      

    report = []
    for chem, qty in usage.items():
        report.append({
            "chemical": chem,
            "kg": round(qty["kg"], 2) if qty["kg"] else None,
            "ltr": round(qty["ltr"], 2) if qty["ltr"] else None
        })
    return render(request, "admin_user/reports/ChemicalsReport.html",
    {
         "records": report,
        "ground_id": ground_id,
        "from_date": from_date,
        "to_date": to_date
    })


# def parse_pass_data(data):
#     if not data or "$##$" not in data:
#         return (0, 0)  # (passes, minutes)

#     value, unit = data.split("$##$")
#     value = value.strip()
#     unit = unit.strip().lower()

#     if unit == "passes":
#         return (int(value), 0)
#     elif unit == "hours":
#         return (0, int(value) * 60)
#     elif unit == "minutes":
#         return (0, int(value))
#     elif unit == "time":
#         try:
#             start_str, end_str = value.split("-")
#             start = datetime.strptime(start_str.strip(), "%H:%M")
#             end = datetime.strptime(end_str.strip(), "%H:%M")
#             delta = end - start
#             return (0, int(delta.total_seconds() / 60))
#         except:
#             return (0, 0)
#     return (0, 0)



def machinery_report(request):
      return render(request, "admin_user/reports/MachineriesReport.html")



def parse_pass_data(data,unit):
        # print(data)
        finalData=[0,0]
   
    
        if unit== "passes":
            finalData[0]+=int(data)
            finalData[1]+=0
        elif unit == "hours":
            finalData[0]+=0
            finalData[1]+=float(data) * 60
            
        elif unit == "minutes":
            finalData[0]+=0
            finalData[1]+=int(data)
            
        elif unit == "time":
            try:
                start_str, end_str = data.split("-")
                start = datetime.strptime(start_str.strip(), "%H:%M")
                end = datetime.strptime(end_str.strip(), "%H:%M")
                delta = end - start
                finalData[0]+=0
                finalData[1]+=int(delta.total_seconds() / 60)
                
            except:
                finalData[0]+=0
                finalData[1]+=0
        # print("finalData=",finalData)
        
        return finalData
    


def machinery_pass_report(request):
    org_id = request.session.get('org_id')
    total_passes = 0
    total_minutes = 0
    ground_id = request.GET.get("ground_id")
    from_date = request.GET.get("from_date")
    to_date = request.GET.get("to_date")
    machinery_id = request.GET.get("machinery_id")
    machinery_name_operator = request.GET.get("machinery_name_operator")

    pass_records = []
    hour_records = []
    machinery_data = {}
    machinery_name = ""
    

    if ground_id and from_date and to_date:
        where_clauses = ["vcd.ground_id = %s", "vcd.rolling_start_date BETWEEN %s AND %s"]
        params = [ground_id, from_date, to_date]

       
        final_where_clause = " AND ".join(where_clauses)
        #  SELECT  
        #         vgm.ground_name,
        #         vcd.no_of_passes, vcd.out_no_of_passes, vcd.practice_no_of_passes, vcd.pp_no_of_passes,
        #         vcd.mowing_duration, vcd.out_mowing_duration, vcd.practice_mowing_duration, vcd.pp_mowing_duration,
        #         vcd.machinery_id, vcd.out_machinery_id, vcd.practice_machinery_id, vcd.pp_machinery_id,
        #         vcd.mover_machinery_id, vcd.out_mover_machinery_id, vcd.practice_mover_machinery_id, vcd.pp_mover_machinery_id,
        #         vcd.roller_machinery_name_operator, vcd.out_roller_machinery_name_operator,
        #         vcd.practice_roller_machinery_name_operator, vcd.pp_roller_machinery_name_operator,
        #         vcd.practice_mover_machinery_name_operator, vcd.pp_mover_machinery_name_operator,
        #         vcd.mover_machinery_name_operator, vcd.out_mover_machinery_name_operator,
        #         vcd.moving_passes_unit, vcd.out_moving_passes_unit, vcd.practice_moving_passes_unit, vcd.pp_moving_passes_unit
        #     FROM {org_id}_curator_daily_recording_master vcd
        #     JOIN {org_id}_ground_master vgm ON vcd.ground_id = vgm.id
        #     WHERE {final_where_clause}
 
        # query = f"""SELECT  
        #         vgm.ground_name,
        #         vcd.no_of_passes, vcd.out_no_of_passes, vcd.practice_no_of_passes, vcd.pp_no_of_passes,
        #         vcd.mowing_duration, vcd.out_mowing_duration, vcd.practice_mowing_duration, vcd.pp_mowing_duration,
        #         vcd.passes_unit, vcd.out_passes_unit, vcd.practice_passes_unit, vcd.pp_passes_unit,
        #         vcd.moving_passes_unit, vcd.out_moving_passes_unit, vcd.practice_moving_passes_unit, vcd.pp_moving_passes_unit,
        #         vcd.machinery_id, vcd.out_machinery_id, vcd.practice_machinery_id, vcd.pp_machinery_id,
        #         vcd.mover_machinery_id, vcd.out_mover_machinery_id, vcd.practice_mover_machinery_id, vcd.pp_mover_machinery_id
        #     FROM {org_id}_curator_daily_recording_master vcd
        #     JOIN {org_id}_ground_master vgm ON vcd.ground_id = vgm.id
        #     WHERE {final_where_clause}"""
            
        query = f"""SELECT  
                vgm.ground_name,
                vcd.no_of_passes, vcd.passes_unit, vcd.machinery_id,
                vcd.out_no_of_passes,vcd.out_passes_unit,vcd.out_machinery_id,
                vcd.practice_no_of_passes,vcd.practice_passes_unit,vcd.practice_machinery_id,
                vcd.pp_no_of_passes, vcd.pp_passes_unit,vcd.pp_machinery_id,
                
                vcd.mowing_duration,vcd.moving_passes_unit, vcd.mover_machinery_id,
                vcd.out_mowing_duration,vcd.out_moving_passes_unit,vcd.out_mover_machinery_id,
                vcd.practice_mowing_duration,vcd.practice_moving_passes_unit,vcd.practice_mover_machinery_id,
                vcd.pp_mowing_duration,vcd.pp_moving_passes_unit,vcd.pp_mover_machinery_id,
                vcd.roller_machinery_name_operator, 
                vcd.out_roller_machinery_name_operator,
                vcd.practice_roller_machinery_name_operator,
                 vcd.pp_roller_machinery_name_operator,
                  vcd.mover_machinery_name_operator,
                  vcd.out_mover_machinery_name_operator,
                  vcd.practice_mover_machinery_name_operator,
                   vcd.pp_mover_machinery_name_operator
                  
                  
                  
                
                
              
            FROM {org_id}_curator_daily_recording_master vcd
            JOIN {org_id}_ground_master vgm ON vcd.ground_id = vgm.id
            WHERE {final_where_clause}"""
        # print(query)
        with connection.cursor() as cursor:
            cursor.execute(query, params)
            records = cursor.fetchall()
            # print(records)
       
        usageList=[]
        
        def split_Data(passes, unit, mid,op):
            if(mid):
                p = passes.split("__####__")
                u = unit.split("__####__")
                m = mid.split("__####__")
                o = op.split("__####__")
                # print(p,u,m,o)
                
                min_len = min(len(p), len(u), len(m),len(o))
                if(machinery_id):
                    for i in range(min_len):
                        m_p = p[i].strip("_#").strip()
                        m_u = u[i].strip("_#").strip()
                        m_m = m[i].strip("_#").strip()
                        m_o = o[i].strip("_#").strip()

                        # âœ… Blank skip karne ke liye condition
                        if m_p or m_u or m_m or m_o:
                            if(m_m==machinery_id):
                                usageList.append({
                                    "pass": m_p,
                                    "unit": m_u,
                                    "mid": m_m,
                                    "mop": m_o
                                })
                else:
                    for i in range(min_len):
                        m_p = p[i].strip("_#").strip()
                        m_u = u[i].strip("_#").strip()
                        m_m = m[i].strip("_#").strip()
                        m_o = o[i].strip("_#").strip()

                        # âœ… Blank skip karne ke liye condition
                        if m_p or m_u or m_m or m_o:
                            usageList.append({
                                    "pass": m_p,
                                    "unit": m_u,
                                    "mid": m_m,
                                    "mop": m_o
                                })
        for row in records:
            split_Data(row[1], row[2], row[3],row[25])   # main pitch
            split_Data(row[4], row[5], row[6],row[26])   # outfield
            split_Data(row[7], row[8], row[9],row[27])   # practice
            split_Data(row[10], row[11], row[12],row[28]) # practice area        
            split_Data(row[13], row[14], row[15],row[29]) # practice area        
            split_Data(row[16], row[17], row[18],row[30]) # practice area        
            split_Data(row[19], row[20], row[21],row[31]) # practice area        
            split_Data(row[22], row[23], row[24],row[32]) # practice area        

        # print(usageList)
        # if machinery_id:
        #     id_query = f"SELECT id, print_details FROM {org_id}_machinery_master WHERE id ='{machinery_id}'"
        #     with connection.cursor() as cursor:
        #             cursor.execute(id_query)
        #             row = cursor.fetchone()
        #             print("Row found for machinery_id=",row)
        #             machinery_name=row[1]
        #             print("machinery_name=",machinery_name)
        # else:
        #     machinery_id="All"
        #     machinery_name="All Machineries"
        
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT  id, print_details FROM {org_id}_machinery_master")
            mid_map = {str(row[0]): row[1] for row in cursor.fetchall()}
            # print(mid_map)
            
        finalList=[]
        if(machinery_id and machinery_name_operator):
            for mrow in usageList:
                if(machinery_id==mrow.get("mid") and machinery_name_operator==mrow.get("mop")):
                    finalList.append({"mid":mrow.get("mid"),"pd":parse_pass_data(mrow.get("pass"),mrow.get("unit"))})
        elif(machinery_id):
            for mrow in usageList:
                if(machinery_id==mrow.get("mid")):
                    finalList.append({"mid":mrow.get("mid"),"pd":parse_pass_data(mrow.get("pass"),mrow.get("unit"))})
        elif(machinery_name_operator):
            for mrow in usageList:
                if(machinery_name_operator.strip()==mrow.get("mop")):
                        finalList.append({"mid":mrow.get("mid"),"pd":parse_pass_data(mrow.get("pass"),mrow.get("unit"))})
        else:
            for mrow in usageList:
                finalList.append({"mid":mrow.get("mid"),"pd":parse_pass_data(mrow.get("pass"),mrow.get("unit"))})
        # print(finalList)
        result = {}

        for entry in finalList:
            mid = entry['mid']
            pd = entry['pd']

            if mid not in result:
                result[mid] = [0, 0]

            # element-wise à¤œà¥‹à¤¡à¤¼à¤¨à¤¾
            result[mid][0] += pd[0]
            result[mid][1] += pd[1]

        # dict à¤¸à¥‡ list of dict à¤¬à¤¨à¤¾à¤¨à¤¾
        finalwithid = [{'mid': mid, 'pd': pd} for mid, pd in result.items()]

        # print(finalwithid)
        
        finalname = []
        for d in finalwithid:
            name = mid_map.get(d['mid'], d['mid'])  # à¤…à¤—à¤° mapping missing à¤¹à¥‹ à¤¤à¥‹ mid à¤¹à¥€ à¤°à¤–à¥‡à¤‚à¤—à¥‡
            finalname.append({'mid': name, 'pd': d['pd']})

        # print(finalname)
        
        
        passes_dict = {}
        minutes_dict = {}

        for d in finalname:
            passes, minutes = d["pd"]
            if passes > 0:   # âœ… à¤•à¥‡à¤µà¤² passes > 0 à¤µà¤¾à¤²à¥‡
                passes_dict[d["mid"]] = passes
            if minutes > 0:  # âœ… à¤•à¥‡à¤µà¤² minutes > 0 à¤µà¤¾à¤²à¥‡
                minutes_dict[d["mid"]] = minutes

        print("Passes Dict:", passes_dict)
        print("Minutes Dict:", minutes_dict)

        

    context = {
        "operator": machinery_name_operator,
    "passes_dict": passes_dict,
    "minutes_dict": minutes_dict,
    "ground_id": ground_id,
    "from_date": from_date,
    "to_date": to_date
    }
    return render(request, "admin_user/reports/MachineriesReport.html", context)



# def machinery_pass_report(request):
#     total_passes = 0
#     total_minutes = 0
#     ground_id = request.GET.get("ground_id")
#     from_date = request.GET.get("from_date")
#     to_date = request.GET.get("to_date")
#     machinery_id = request.GET.get("machinery_id")
#     machinery_name_operator = request.GET.get("machinery_name_operator")

#     pass_records = []
#     hour_records = []
#     machinery_data = {}
#     machinery_names = {}

#     if ground_id and from_date and to_date:
#         query = """
#             SELECT vgm.ground_name, 
#                    vcd.no_of_passes, vcd.out_no_of_passes, vcd.practice_no_of_passes, vcd.pp_no_of_passes,
#                    vcd.machinery_id, vcd.out_machinery_id, vcd.practice_machinery_id, vcd.pp_machinery_id
#             FROM {org_id}_curator_daily_recording_master vcd
#             JOIN {org_id}_ground_master vgm ON vcd.ground_id = vgm.id
#             WHERE vcd.ground_id = %s AND vcd.machinery_id=%s OR vcd.out_machinery_id=%s OR vcd.practice_machinery_id=%s OR vcd.pp_machinery_id=%s AND 
#             roller_machinery_name_operator=%s OR pp_roller_machinery_name_operator =%s OR out_roller_machinery_name_operator=%s OR practice_roller_machinery_name_operator=%s 
            
#             AND rolling_start_date BETWEEN %s AND %s
#         """
#         with connection.cursor() as cursor:
#             cursor.execute(query, [ground_id, from_date, to_date])
#             records = cursor.fetchall()

#         # Collect unique machinery IDs
#         machinery_ids = set()
#         for row in records:
#             machinery_columns = row[5:9]
#             for mid in machinery_columns:
#                 if mid:
#                     machinery_ids.add(mid)

#         # Map machinery IDs to print_details
#         if machinery_ids:
#             placeholders = ",".join(["%s"] * len(machinery_ids))
#             id_query = f"SELECT id, print_details FROM {org_id}_machinery_master WHERE id IN ({placeholders})"
#             with connection.cursor() as cursor:
#                 cursor.execute(id_query, list(machinery_ids))
#                 for mid, name in cursor.fetchall():
#                     machinery_names[str(mid)] = name

#         # Process each record
#         for row in records:
#             ground_name = row[0]
#             pass_columns = row[1:5]
#             machinery_columns = row[5:9]

#             for i in range(4):
#                 machinery_id = str(machinery_columns[i]) if machinery_columns[i] else "Unknown"
#                 # machinery_name = machinery_names.get(machinery_id, "Unknown")
#                 machinery_name = machinery_names.get(machinery_id, f"Unknown (ID: {machinery_id})")


#                 passes, minutes = parse_pass_data(pass_columns[i])

#                 if machinery_name not in machinery_data:
#                     machinery_data[machinery_name] = {"passes": 0, "minutes": 0}

#                 machinery_data[machinery_name]["passes"] += passes
#                 machinery_data[machinery_name]["minutes"] += minutes

#                 total_passes += passes
#                 total_minutes += minutes

#         # Prepare separate records for passes and hours
#         for machine, stats in machinery_data.items():
#             pass_records.append({
#                 "machinery": machine,
#                 "total_passes": stats["passes"]
#             })
#             hour_records.append({
#                 "machinery": machine,
#                 "total_hours": round(stats["minutes"] / 60, 2)
#             })

#     context = {
#         "pass_records": pass_records,
#         "hour_records": hour_records,
#         "total_passes": total_passes,
#         "total_hours": round(total_minutes / 60, 2),
#         "ground_id": ground_id,
#         "from_date": from_date,
#         "to_date": to_date
#     }
#     return render(request, "admin_user/reports/MachineriesReport.html", context)



######################end reports

def groundform(request):
    return render(request,'admin_user/ground_form.html')

def login(request):
    return render(request,'admin_user/org_login.html')

def curatorLogin(request):
    return render(request,'curator/org_login.html')

def groundmanLogin(request):
    return render(request,'groundman/org_login.html')

def scorerLogin(request):
    return render(request,'scorer/org_login.html')


def get_fertilizers_json(request):
    org_id = request.session.get('org_id')
    with connection.cursor() as cursor:
        cursor.execute(f"SELECT id, chemical_name,chemical_type FROM {org_id}_fertilizer_master")
        data = cursor.fetchall()
    result = [{"id": row[0], "name": row[1],"type":row[2]} for row in data]
    return JsonResponse({"fertilizers": result})

def get_single_fertilizer(request, fert_id):
    org_id = request.session.get('org_id')
    with connection.cursor() as cursor:
        cursor.execute(f"SELECT id, chemical_name, chemical_type FROM {org_id}_fertilizer_master WHERE id = %s", [fert_id])
        row = cursor.fetchone()
    
    if row:
        result = {"id": row[0], "name": row[1], "type": row[2]}
        return JsonResponse(result)
    else:
        return JsonResponse({"error": "Chemical not found"}, status=404)

def get_unique_chemical_types(request):
    org_id = request.session.get('org_id')
    with connection.cursor() as cursor:
        cursor.execute(f"SELECT DISTINCT chemical_type FROM {org_id}_fertilizer_master")
        rows = cursor.fetchall()

    types = [row[0] for row in rows]
    return JsonResponse({"types": types})

def fertilizer_list(request):
    try:
        org_id = request.session.get('org_id')
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT id, chemical_name,chemical_type FROM {org_id}_fertilizer_master")
            fertilizers = cursor.fetchall()
            print(fertilizers)
        return render(request, 'admin_user/masters/chemicals_list.html', {'fertilizers': fertilizers})
    except Exception as e:
        print(e)

def fertilizer_add(request):
    try:
        org_id = request.session.get('org_id')
        if request.method == 'POST':
            chemical_name = request.POST.get('chemical_name')
            chemical_type_select = request.POST.get('chemical_type_select')
            with connection.cursor() as cursor:
                cursor.execute(f"INSERT INTO {org_id}_fertilizer_master (chemical_name,chemical_type) VALUES (%s,%s)", [chemical_name,chemical_type_select])
            return redirect('fertilizer_list')
        return render(request, 'admin_user/masters/chemical_add.html')
    except Exception as e:
        print(e)


def fertilizer_edit(request, id):
    try:
        org_id = request.session.get('org_id')
        if request.method == 'POST':
            chemical_name = request.POST.get('chemical_name')
            chemical_type_select = request.POST.get('chemical_type_select')
            with connection.cursor() as cursor:
                cursor.execute(f"UPDATE {org_id}_fertilizer_master SET chemical_name=%s,chemical_type=%s WHERE id=%s", [chemical_name,chemical_type_select,id])
            return redirect('fertilizer_list')
        else:
            with connection.cursor() as cursor:
                print(id)
                cursor.execute(f"SELECT id, chemical_name,chemical_type FROM {org_id}_fertilizer_master WHERE id=%s", [id])
                fertilizer = cursor.fetchone()
                print(fertilizer)
            return render(request, 'admin_user/masters/chemical_edit.html', {'fertilizer': fertilizer})
    except Exception as e:
        print(e)


def fertilizer_delete(request, id):
    try:
        org_id = request.session.get('org_id')
        with connection.cursor() as cursor:
            cursor.execute(f"DELETE FROM {org_id}_fertilizer_master WHERE id=%s", [id])
        return redirect('fertilizer_list')
    except Exception as e:
        print(e)



def login_auth(request):
    if request.method == 'POST':
        org_id = request.POST.get('org_id')
        username = request.POST.get('username')
        password = request.POST.get('password')
        # print(org_id)
        try:
            user = AdminUserList.objects.get( org_id=org_id,username=username, password=password)
            if user is not None:
                request.session["org_id"]=user.org_id
                request.session["user"] = {
                    "id": user.id,
                    "name": user.name,
                    "org_id": user.org_id,
                    "email": user.email,
                    "username": user.username,
                    "address":user.address,
                    "role": "admin",
                    "ground_id":"all"
                    
                    
                }
                print(request.session.get("user"))
                
                return render(request,'admin_user/dashboard.html',{'user':user})
            else:
                messages.error(request, 'Invalid username or password')
                return render(request, 'admin_user/org_login.html')
        except Exception as e:
            print(e)
            return render(request, 'admin_user/org_login.html')



def login_auth_role(request):

    if request.method == 'POST':
        org_id = request.POST.get('org_id')
        username = request.POST.get('username')
        password = request.POST.get('password')
        role = request.POST.get('role')
        
        try:
            user = AdminRole.objects.get( org_id=org_id,username=username, password=password,role=role)
            admin = AdminUserList.objects.get( org_id=org_id)

            if user is not None:
                request.session["org_id"]=user.org_id
                request.session["user"] = {
                    "id": user.id,
                    "name": user.name,
                    "org_id": user.org_id,
                    "email": user.email,
                    "username": user.username,
                    "ground_id":user.ground_id,
                    "role": user.role
                }
                profilePath = user.profileImage.url
                if(role=="Groundman"):
                    return render(request,'groundman/dashboard.html',{'user':user,'profilePath':profilePath,"admin":admin})
                elif(role=="Curator"):
                    return render(request,'curator/dashboard.html',{'user':user,'profilePath':profilePath,"admin":admin})
                elif(role=="Scorer"):
                    return render(request,'scorer/dashboard.html',{'user':user,'profilePath':profilePath,"admin":admin})

            else:
                messages.error(request, 'Invalid username or password')
        except Exception as e:
            print(e)
            if (role == "Groundman"):
                return render(request, 'groundman/org_login.html')
            elif (role == "Curator"):
                return render(request, 'curator/org_login.html')
            elif (role == "Scorer"):
                return render(request, 'scorer/org_login.html')


def login_auth_role_direct(request):

    if request.method == 'GET':
        org_id = request.session.get('org_id')
      
        role = request.GET.get('role')
        
        id = request.GET.get('id')
        
        try:
            user = AdminRole.objects.get( org_id=org_id,id=id,role=role)
           

            if user is not None:
                request.session["org_id"]=user.org_id
                request.session["userdirect"] = {
                    "id": user.id,
                    "name": user.name,
                    "org_id": user.org_id,
                    "email": user.email,
                    "username": user.username,
                    "ground_id":user.ground_id,
                    "role": user.role
                }
                profilePath = user.profileImage.url
                if(role=="Groundman"):
                    return render(request,'groundman/dashboard.html',{'user':user,'profilePath':profilePath})
                elif(role=="Curator"):
                    return render(request,'curator/dashboard.html',{'user':user,'profilePath':profilePath})
                elif(role=="Scorer"):
                    return render(request,'scorer/dashboard.html',{'user':user,'profilePath':profilePath})

            else:
                messages.error(request, 'Invalid username or password')
        except Exception as e:
            print(e)
            if (role == "Groundman"):
                return render(request, 'groundman/org_login.html')
            elif (role == "Curator"):
                return render(request, 'curator/org_login.html')
            elif (role == "Scorer"):
                return render(request, 'scorer/org_login.html')




def org_dashboard(request):
    user_id = request.session.get("user").get("id")  # Retrieve the stored ID from the session
    if user_id:
        try:
            user = AdminUserList.objects.get(id=user_id)  # Retrieve the user object from the database
            return render(request, 'admin_user/dashboard.html', {'user': user})
        except AdminUserList.DoesNotExist:
            org_user = None  # Handle the case where the user does not exist

def getCurators(request):
    org_id = request.session.get('org_id')
    with connection.cursor() as cursor:
        cursor.execute(f"SELECT id, name FROM admin_user_adminrole WHERE role='Curator' and org_id='{org_id}'")
        curators = cursor.fetchall()
    return JsonResponse({"curators": curators})

def getGroundmans(request):
    org_id = request.session.get('org_id')
    with connection.cursor() as cursor:
        cursor.execute(f"SELECT id, name FROM admin_user_adminrole WHERE role='Groundman' and org_id='{org_id}'")
        groundmans = cursor.fetchall()
    return JsonResponse({"groundmans":  groundmans})

def getScorers(request):
    org_id = request.session.get('org_id')
    with connection.cursor() as cursor:
        cursor.execute(f"SELECT id, name FROM admin_user_adminrole WHERE role='Scorer' and org_id='{org_id}'")
        scorers = cursor.fetchall()
    return JsonResponse({"scorers": scorers})


def role_dashboard(request):
    return render(request,'admin_user/dashboard_role.html')

def logout_view(request):
    return redirect('login')

def add_state_city(request):
    org_id = request.session.get('org_id')
    if request.method == 'POST':
        try:
            state_name = request.POST.get('state').split("-")[1].strip()
            state_code = request.POST.get('state-code')
            city_name = request.POST.get('city')
            with connection.cursor() as cursor:
                print("Method Post")
                cursor.execute(f'''INSERT INTO {org_id}_state_master (state, state_code) VALUES (%s, %s)''',
                               [state_name, state_code])

                cursor.execute(f'SELECT id FROM {org_id}_state_master WHERE state = %s', [state_name])
                state_id = cursor.fetchone()[0]

                # Insert city data
                cursor.execute(f'''INSERT INTO {org_id}_city_master (city_name, state_id) VALUES (%s, %s)''',
                               [city_name, state_id])

                return redirect('list_state_city')



        except Exception as e:
            print(e)
            # messages.error(request, e)
            with connection.cursor() as cursor:
                cursor.execute(f'SELECT id FROM {org_id}_state_master WHERE state = %s', [state_name])
                state_id = cursor.fetchone()[0]

                # Insert city data
                cursor.execute(f'''INSERT INTO {org_id}_city_master (city_name, state_id) VALUES (%s, %s)''',
                               [city_name, state_id])

                return redirect('list_state_city')

        # Insert state data if not already present

    else:
        print("Method GET")
        return render(request, 'admin_user/masters/add_state_city.html')
        # form = StateCityForm(request)


def list_state_city(request):
    org_id = request.session.get('org_id')
    with connection.cursor() as cursor:
        cursor.execute(f'''
            SELECT s.state, s.state_code, c.city_name
            FROM {org_id}_state_master s
            LEFT JOIN {org_id}_city_master c ON s.id = c.state_id
        ''')
        state_city_data = cursor.fetchall()

    return render(request, 'admin_user/masters/list_state_city.html', {'state_city_data': state_city_data})


def create_admin_user_role(request):

    try:
        if request.method == 'POST':
            form = AdminUserRoleForm(request.POST, request.FILES)
            if form.is_valid():
                try:
                    instance=form.save()
                    messages.success(request, 'Admin user created successfully')
                    # createAllMastersTables(instance)
                    return redirect('/usr_admin/admin_users_roles_list')  # Redirect to a view that lists admin users
                except Exception as e:
                    messages.error(request, e)
            else:
                messages.error(request, form.errors)
        else:
            form = AdminUserRoleForm(initial={'org_id':request.session["org_id"]})
        return render(request, 'admin_user/create_admin_role.html', {'form': form})
    except Exception as e:
        messages.error(request, e)
        print(e)

def admin_user_roles_list(request):
    org_id = request.session["org_id"]
    admin_roles = AdminRole.objects.filter(org_id=org_id)
    print(admin_roles)
    return render(request, 'admin_user/admin_users_roles_list.html', {'admin_roles': admin_roles})

def admin_user_role_details(request, admin_id):
    admin = AdminRole.objects.get(id=admin_id)
    profilePath=admin.profileImage.url
    # print(profilePath)
    return render(request, 'admin_user/admin_user_role_details.html', {'admin': admin,'profilePath':profilePath})

def create_ground_master(request):
   
    try:
        org_id = request.session["org_id"]
        if request.method == "POST":
            org_id = request.POST.get('org_id')
            google_location = request.POST.get('google_location')
            year_of_construction = request.POST.get('year_of_construction')
            phone_numbers = request.POST.get('phone_numbers')
            slop_ratio = request.POST.get('slop_ratio')
            ground_name = request.POST.get('ground_name')
            state_code = request.POST.get('state_code')
            state_name = request.POST.get('state_name')
            city_name = request.POST.get('city_name')
            count_main_pitches = request.POST.get('count_main_pitches')
            count_practice_pitches = request.POST.get('count_practice_pitches')
            is_side_screen = request.POST.get('is_side_screen',False)
            # print("is_side_screen",is_side_screen)
            count_placement_side_screen = 0 
            is_broadcasting_facility = request.POST.get('is_broadcasting_facility', False)
            is_irrigation_pitches = request.POST.get('is_irrigation_pitches', False)
            count_hydrants = request.POST.get('count_hydrants')
            count_pumps = request.POST.get('count_pumps')
            # count_showers = request.POST.get('count_showers')
            is_lawn_nursary = request.POST.get('is_lawn_nursary', False)
            name_centre_square = ""
            is_curator_room = request.POST.get('is_curator_room', False)
            is_seperate_practice_area = request.POST.get('is_seperate_practice_area', False)
            # outfield = request.POST.get('outfield')
            profile_of_outfield = request.POST.get('profile_of_outfield')
            lawn_species = request.POST.get('lawn_species')
            is_drainage_system_available = request.POST.get('is_drainage_system_available', False)
            is_water_drainage_system = ""
            is_irrigation_system_available = request.POST.get('is_irrigation_system_available', False)
            is_availability_of_water = request.POST.get('is_availability_of_water', False)
            water_source = request.POST.get('water_source')
            storage_capacity_in_litres = request.POST.get('storage_capacity_in_litres')
            count_pop_ups = request.POST.get('count_pop_ups')
            size_of_pumps = request.POST.get('size_of_pumps')
            is_automation_if_any = request.POST.get('is_automation_if_any', False)
            is_ground_equipments = request.POST.get('is_ground_equipments', False)
            is_maintenance_contract = request.POST.get('is_maintenance_contract', False)
            is_maintenance_agency = request.POST.get('is_maintenance_agency', False)
            boundary_size_mtrs = f'''{request.POST.get('boundary_size_mtrs-E')}#{request.POST.get('boundary_size_mtrs-W')}#{request.POST.get('boundary_size_mtrs-N')}#{request.POST.get('boundary_size_mtrs-S')}'''
            is_availability_of_mot = request.POST.get('is_availability_of_mot', False)
            is_machine_shed = request.POST.get('is_machine_shed', False)
            is_soil_shed = request.POST.get('is_soil_shed', False)
            is_pitch_or_run_up_covers = request.POST.get('is_pitch_or_run_up_covers', False)
            size_of_covers_in_mtrs = request.POST.get('size_of_covers_in_mtrs')
            screen_size = request.POST.get('screen_size')
            broadcast_video_analysis = request.POST.get('broadcast_video_analysis')
            outfield_type = request.POST.get('outfield_type')
            lawn_species_out = request.POST.get('lawn_species_out')

            with connection.cursor() as cursor:
                # Insert into Ground Master table
                cursor.execute(f'''
                            SELECT state, state_code
                            FROM {org_id}_state_master''')
                state_data = cursor.fetchall()
                cursor.execute(
                    f"""INSERT INTO {org_id}_ground_master (
                        org_id, google_location, year_of_construction ,phone_numbers ,slop_ratio, ground_name, state_code, state_name, 
                        city_name, count_main_pitches, count_practice_pitches, 
                        is_side_screen, count_placement_side_screen, is_broadcasting_facility, is_irrigation_pitches, count_hydrants, 
                        count_pumps, is_lawn_nursary, name_centre_square, is_curator_room, is_seperate_practice_area, 
                         profile_of_outfield, lawn_species, is_drainage_system_available,
                        is_irrigation_system_available, is_availability_of_water, water_source, storage_capacity_in_litres, 
                        count_pop_ups, size_of_pumps, is_automation_if_any, is_ground_equipments, is_maintenance_contract, 
                        is_maintenance_agency, boundary_size_mtrs, is_availability_of_mot, is_machine_shed, is_soil_shed, 
                        is_pitch_or_run_up_covers, size_of_covers_in_mtrs,screen_size,broadcast_video_analysis,outfield_type,lawn_species_out) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s,%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                    [org_id, google_location,year_of_construction,phone_numbers,slop_ratio,ground_name, state_code, state_name, city_name, count_main_pitches, count_practice_pitches,
                     is_side_screen, count_placement_side_screen, is_broadcasting_facility, is_irrigation_pitches,
                     count_hydrants,
                     count_pumps, is_lawn_nursary, name_centre_square, is_curator_room,
                     is_seperate_practice_area,
                      profile_of_outfield, lawn_species, is_drainage_system_available,
                    #  is_water_drainage_system,
                     is_irrigation_system_available, is_availability_of_water, water_source,
                     storage_capacity_in_litres,
                     count_pop_ups, size_of_pumps, is_automation_if_any, is_ground_equipments, is_maintenance_contract,
                     is_maintenance_agency, boundary_size_mtrs, is_availability_of_mot, is_machine_shed, is_soil_shed,
                     is_pitch_or_run_up_covers, size_of_covers_in_mtrs,screen_size,
                      broadcast_video_analysis, outfield_type,lawn_species_out]
                )
                ground_id = cursor.lastrowid  # Get the ID of the newly inserted ground
                cursor.execute(
                        f"INSERT INTO {org_id}_pitch_master (org_id, ground_id, pitch_no,pitch_type,pitch_placement) VALUES (%s, %s, %s,%s,%s)",
                        [org_id, ground_id, 0,"area","all"])
                # Insert into Pitch Master table
                # total_pitches = int(count_main_pitches) + int(count_practice_pitches)
                i=1
                while(i<=int(count_main_pitches)):
                    cursor.execute(
                        f"INSERT INTO {org_id}_pitch_master (org_id, ground_id, pitch_no,pitch_type) VALUES (%s, %s, %s,%s)",
                        [org_id, ground_id, i,"main"]

                    )
                    i+=1

                i=1
                while(i<=int(count_practice_pitches)):
                    cursor.execute(
                        f"INSERT INTO {org_id}_pitch_master (org_id, ground_id, pitch_no,pitch_type) VALUES (%s, %s, %s,%s)",
                        [org_id, ground_id, i,"practice"]

                    )
                    i+=1
                # for i in range(1, total_pitches + 1):
                #     cursor.execute(
                #         f"INSERT INTO {org_id}_pitch_master (org_id, ground_id, pitch_no,pitch_type) VALUES (%s, %s, %s,%s)",
                #         [org_id, ground_id, i]
                #     )
            return redirect('ground_pitches',ground_id)
        with connection.cursor() as cursor:
                # Insert into Ground Master table
                cursor.execute(f'''
                            SELECT id,state, state_code
                            FROM {org_id}_state_master''')
                state_data = cursor.fetchall()
                print(state_data)
        return render(request, 'admin_user/create_ground_master.html',{'org_id':request.session["org_id"],'state_data':state_data})
    except Exception as e:
        print(e)

def update_ground_master(request, ground_id):
    try:
        org_id = request.session.get("org_id")
        with connection.cursor() as cursor:
            cursor.execute(f'SELECT * FROM {org_id}_ground_master WHERE id = %s', [ground_id])
            ground = cursor.fetchone()

        if request.method == "POST":
                org_id = request.POST.get('org_id')
                google_location = request.POST.get('google_location')
                year_of_construction = request.POST.get('year_of_construction')
                phone_numbers = request.POST.get('phone_numbers')
                old_phone_numbers = request.POST.get('oldPhoneNumbers')
                if(phone_numbers!=old_phone_numbers):
                    phone_numbers=old_phone_numbers.strip()+", "+phone_numbers.strip()

                
                slop_ratio = request.POST.get('slop_ratio')
                lawn_species_out = request.POST.get('lawn_species_out')
                broadcast_video_analysis = request.POST.get('broadcast_video_analysis')
                outfield_type = request.POST.get('outfield_type')
                ground_name = request.POST.get('ground_name')
                state_code = request.POST.get('state_code')
                state_name = request.POST.get('state_name')
                city_name = request.POST.get('city_text')
                count_main_pitches = request.POST.get('count_main_pitches')
                count_practice_pitches = request.POST.get('count_practice_pitches')
                is_side_screen = True if request.POST.get('is_side_screen',False)=="on" else False
                print(is_side_screen)
                # print("is_side_screen",is_side_screen)
                count_placement_side_screen = 0 
                is_broadcasting_facility = True if request.POST.get('is_broadcasting_facility',False)=="on" else False
                is_irrigation_pitches =  True if request.POST.get('is_irrigation_pitches',False)=="on" else False
                count_hydrants = request.POST.get('count_hydrants')
                count_pumps = request.POST.get('count_pumps')
                # count_showers = request.POST.get('count_showers')
                is_lawn_nursary = True if request.POST.get('is_lawn_nursary',False)=="on" else False
                name_centre_square = ""
                is_curator_room =True if request.POST.get('is_curator_room',False)=="on" else False
                is_seperate_practice_area =  True if request.POST.get('is_seperate_practice_area',False)=="on" else False
                # outfield = request.POST.get('outfield')
                profile_of_outfield = request.POST.get('profile_of_outfield')
                lawn_species = request.POST.get('lawn_species')
                is_drainage_system_available =  True if request.POST.get('is_drainage_system_available',False)=="on" else False
                is_water_drainage_system = ""
                is_irrigation_system_available =  True if request.POST.get('is_irrigation_system_available',False)=="on" else False
                is_availability_of_water =True if request.POST.get('is_availability_of_water',False)=="on" else False
                water_source = request.POST.get('water_source')
                storage_capacity_in_litres = request.POST.get('storage_capacity_in_litres')
                count_pop_ups = request.POST.get('count_pop_ups')
                size_of_pumps = request.POST.get('size_of_pumps')
                is_automation_if_any = True if request.POST.get('is_automation_if_any',False)=="on" else False
                is_ground_equipments = True if request.POST.get('is_ground_equipments',False)=="on" else False
                is_maintenance_contract =  True if request.POST.get('is_maintenance_contract',False)=="on" else False
                is_maintenance_agency =  True if request.POST.get('is_maintenance_agency',False)=="on" else False
                boundary_size_mtrs = f'''{request.POST.get('boundary_size_mtrs-E')}#{request.POST.get('boundary_size_mtrs-W')}#{request.POST.get('boundary_size_mtrs-N')}#{request.POST.get('boundary_size_mtrs-S')}'''
                is_availability_of_mot = True if request.POST.get('is_availability_of_mot',False)=="on" else False
                is_machine_shed = True if request.POST.get('is_machine_shed',False)=="on" else False
                is_soil_shed =True if request.POST.get('is_soil_shed',False)=="on" else False
                is_pitch_or_run_up_covers = True if request.POST.get('is_pitch_or_run_up_covers',False)=="on" else False
                size_of_covers_in_mtrs = request.POST.get('size_of_covers_in_mtrs')
                screen_size = request.POST.get('screen_size')
                broadcast_video_analysis = request.POST.get('broadcast_video_analysis')
                outfield_type = request.POST.get('outfield_type')

                with connection.cursor() as cursor:
                    # Insert into Ground Master table
                    cursor.execute(f'''
                                SELECT state, state_code
                                FROM {org_id}_state_master''')
                    state_data = cursor.fetchall()
                    cursor.execute(
                        f"""update {org_id}_ground_master set
                            org_id=%s, 
                            google_location=%s,
                            year_of_construction=%s ,
                            phone_numbers=%s ,
                            slop_ratio=%s, 
                            ground_name=%s, 
                            state_code=%s, 
                            state_name=%s, 
                            city_name=%s, 
                            count_main_pitches=%s, 
                            count_practice_pitches=%s, 
                            is_side_screen=%s, 
                            count_placement_side_screen=%s, 
                            is_broadcasting_facility=%s, 
                            is_irrigation_pitches=%s, 
                            count_hydrants=%s, 
                            count_pumps=%s, 
                            is_lawn_nursary=%s, 
                            name_centre_square=%s, 
                            is_curator_room=%s, 
                            is_seperate_practice_area=%s, 
                            profile_of_outfield=%s, 
                            lawn_species=%s, 
                            is_drainage_system_available=%s,
                            is_irrigation_system_available=%s, 
                            is_availability_of_water=%s, 
                            water_source=%s, 
                            storage_capacity_in_litres=%s, 
                            count_pop_ups=%s, 
                            size_of_pumps=%s, 
                            is_automation_if_any=%s, 
                            is_ground_equipments=%s, 
                            is_maintenance_contract=%s, 
                            is_maintenance_agency=%s, 
                            boundary_size_mtrs=%s, 
                            is_availability_of_mot=%s, 
                            is_machine_shed=%s, 
                            is_soil_shed=%s, 
                            is_pitch_or_run_up_covers=%s, 
                            size_of_covers_in_mtrs=%s,
                            screen_size = %s,
                            broadcast_video_analysis=%s, 
                            lawn_species_out=%s,
                            outfield_type=%s
                            where id=%s""",
                        [org_id, 
                         google_location,
                         year_of_construction,
                         phone_numbers,
                         slop_ratio,
                         ground_name, 
                         state_code, 
                         state_name, 
                         city_name, 
                         count_main_pitches, 
                         count_practice_pitches,
                        is_side_screen, 
                        count_placement_side_screen, 
                        is_broadcasting_facility, 
                        is_irrigation_pitches,
                        count_hydrants,
                        count_pumps,
                        is_lawn_nursary, 
                        name_centre_square, 
                        is_curator_room,
                        is_seperate_practice_area,
                        profile_of_outfield, 
                        lawn_species, 
                        is_drainage_system_available,
                        #  is_water_drainage_system,
                        is_irrigation_system_available, 
                        is_availability_of_water, 
                        water_source,
                        storage_capacity_in_litres,
                        count_pop_ups, 
                        size_of_pumps, 
                        is_automation_if_any, 
                        is_ground_equipments, 
                        is_maintenance_contract,
                        is_maintenance_agency, 
                        boundary_size_mtrs, 
                        is_availability_of_mot, 
                        is_machine_shed, 
                        is_soil_shed,
                        is_pitch_or_run_up_covers, 
                        size_of_covers_in_mtrs,
                        screen_size,
                        broadcast_video_analysis,
                        lawn_species_out,
                        outfield_type,
                        ground_id]
                    )
                  
                return redirect('ground_pitches',ground_id)
        with connection.cursor() as cursor:
                    # Insert into Ground Master table
                    cursor.execute(f'''
                                SELECT id,state, state_code
                                FROM {org_id}_state_master''')
                    state_data = cursor.fetchall()
                    print(state_data)
        return render(request, 'admin_user/update_ground_master.html',
                      {'org_id':request.session["org_id"],'state_data':state_data,"ground":ground})
    except Exception as e:
        print(e)
    

@csrf_exempt
def delete_ground_master(request, ground_id):
    try:
        org_id = request.session["org_id"]
        if request.method == 'DELETE':
            with connection.cursor() as cursor:
                # Delete score by id
                cursor.execute(f"""DELETE FROM {org_id}_ground_master WHERE id = %s""", [ground_id])
                cursor.execute(f"""DELETE FROM {org_id}_pitch_master WHERE ground_id = %s""", [ground_id])

            return JsonResponse({'status':True,'msg': 'success'})
        else:
            return JsonResponse({'status':False,'msg': 'failed'})
    except Exception as e:
        print(e)
        return JsonResponse({'status':False,'msg': f'failed error:{e}'})

@csrf_exempt
def addNewPItch(request):
    try:
        if request.method == 'POST':
            org_id = request.session["org_id"]
            ground_id = request.POST.get("ground_id")
            pitch_type = request.POST.get("pitch_type")
            pitch_no=-1
            print(pitch_type)
            
            with connection.cursor() as cursor:
                # Delete score by id
                cursor.execute(f"""Select * FROM {org_id}_ground_master WHERE id = %s""", [ground_id])
                ground=cursor.fetchone()
                if(pitch_type=="main"):
                    main=ground[10]
                    pitch_no=main+1
                    
                elif(pitch_type=="practice"):
                    practice=ground[11]
                    pitch_no=practice+1

                cursor.execute(f"""INSERT INTO {org_id}_pitch_master 
                               (`org_id`,`ground_id`,`pitch_no`,`pitch_type`) 
                               VALUES ('{org_id}','{ground_id}','{pitch_no}','{pitch_type}')""")
                
                if(pitch_type=="main"):
                    cursor.execute(f"""update {org_id}_ground_master set count_main_pitches=%s WHERE id = %s""", [pitch_no, ground_id])
                elif(pitch_type=="practice"):
                    cursor.execute(f"""update {org_id}_ground_master set count_practice_pitches=%s WHERE id = %s""", [pitch_no, ground_id])

                

                
            return JsonResponse({'status':True,'msg': 'success'})
        else:
            return JsonResponse({'status':False,'msg': 'failed'})
    except Exception as e:
        print(e)
        return JsonResponse({'status':False,'msg': f'failed error:{e}'})


@csrf_exempt
def update_pitches(request, ground_id):
    org_id = request.session.get("org_id")
    with connection.cursor() as cursor:
        cursor.execute(f'SELECT * FROM {org_id}_ground_master WHERE id = %s', [ground_id])
        ground = cursor.fetchone()

        cursor.execute(f'SELECT * FROM {org_id}_pitch_master WHERE ground_id = %s', [ground_id])
        pitches = cursor.fetchall()

    if request.method == 'POST':
        form = PitchMasterForm(request.POST, pitches=pitches)
        if form.is_valid():
            with transaction.atomic():
                with connection.cursor() as cursor:
                    for pitch in pitches:
                        pitch_id = pitch[0]
                        pitch_data = {
                            'pitch_no': form.cleaned_data[f'pitch_no_{pitch_id}'],
                            'pitch_type': form.cleaned_data[f'pitch_type_{pitch_id}'],
                            'profile_of_pitches': form.cleaned_data[f'profile_of_pitches_{pitch_id}'],
                            'size_pitch_square': form.cleaned_data[f'size_pitch_square_{pitch_id}'],
                            'last_used_date': form.cleaned_data[f'last_used_date_{pitch_id}'],
                            'last_used_match': form.cleaned_data[f'last_used_match_{pitch_id}'],
                            'is_uniformtiy_of_grass': form.cleaned_data[f'is_uniformtiy_of_grass_{pitch_id}'],
                            'size_of_grass': form.cleaned_data[f'size_of_grass_{pitch_id}'],
                            'mowing_last_date': form.cleaned_data[f'mowing_last_date_{pitch_id}'],
                            'mowing_size': form.cleaned_data[f'mowing_size_{pitch_id}'],
                            'start_date_of_pitch_preparation': form.cleaned_data[
                                f'start_date_of_pitch_preparation_{pitch_id}'],
                            'date_of_pitch_construction': form.cleaned_data[
                                f'date_of_pitch_construction_{pitch_id}'],
                            'soil_type': form.cleaned_data[f'soil_type_{pitch_id}']
                        }
                        cursor.execute(f'''
                                UPDATE {org_id}_pitch_master SET
                                    pitch_no = %s, pitch_type = %s, profile_of_pitches = %s,size_pitch_square=%s, last_used_date = %s,
                                    last_used_match = %s, is_uniformtiy_of_grass = %s, size_of_grass = %s, mowing_last_date = %s,
                                    mowing_size = %s, start_date_of_pitch_preparation = %s,date_of_pitch_construction = %s, soil_type = %s
                                WHERE id = %s
                            ''', (
                            pitch_data['pitch_no'], pitch_data['pitch_type'], pitch_data['profile_of_pitches'],
                            pitch_data['size_pitch_square'],pitch_data['last_used_date'],
                            pitch_data['last_used_match'], pitch_data['is_uniformtiy_of_grass'],
                            pitch_data['size_of_grass'], pitch_data['mowing_last_date'],
                            pitch_data['mowing_size'], pitch_data['start_date_of_pitch_preparation'],
                            pitch_data['date_of_pitch_construction'],pitch_data['soil_type'], pitch_id
                        ))
            return redirect('ground_list')
    else:
        initial_data = {}
        for pitch in pitches:
            pitch_id = pitch[0]
            initial_data[f'pitch_no_{pitch_id}'] = pitch[3]
            initial_data[f'pitch_type_{pitch_id}'] = pitch[4]
            initial_data[f'profile_of_pitches_{pitch_id}'] = pitch[5]
            initial_data[f'size_pitch_square_{pitch_id}'] = pitch[17]
            initial_data[f'last_used_date_{pitch_id}'] = pitch[6]
            initial_data[f'last_used_match_{pitch_id}'] = pitch[7]
            initial_data[f'is_uniformtiy_of_grass_{pitch_id}'] = pitch[8]
            initial_data[f'size_of_grass_{pitch_id}'] = pitch[9]
            initial_data[f'mowing_last_date_{pitch_id}'] = pitch[10]
            initial_data[f'mowing_size_{pitch_id}'] = pitch[11]
            initial_data[f'start_date_of_pitch_preparation_{pitch_id}'] = pitch[12]
            initial_data[f'date_of_pitch_construction_{pitch_id}'] = pitch[16]
            initial_data[f'soil_type_{pitch_id}'] = pitch[13]
        form = PitchMasterForm(initial=initial_data, pitches=pitches)
        # print(form)
    # return render(request, 'update_pitches.html', {'form': form, 'ground': ground})

    return render(request, 'admin_user/update_pitches.html', {
        'form': form,
        'ground': {
            'id': ground[0],
            'name': ground[1],  # Assuming the second column is the ground name
        },
        'pitches': [{'id': pitch[0]} for pitch in pitches]

    })

def ground_list(request):
    org_id = request.session["org_id"]
    with connection.cursor() as cursor:
        cursor.execute(f'SELECT * FROM {org_id}_ground_master')
        grounds = cursor.fetchall()

    return render(request, 'admin_user/ground_list.html', {'grounds': grounds})

def ground_pitches(request,ground_id):
    try:
        org_id = request.session["org_id"]
        with connection.cursor() as cursor:
            cursor.execute(f'SELECT * FROM {org_id}_ground_master where id=%s',[ground_id])
            grounds = cursor.fetchall()

        with connection.cursor() as cursor:
            cursor.execute(f'''SELECT * FROM {org_id}_pitch_master WHERE ground_id = %s''', [ground_id])
            pitches = cursor.fetchall()
        return render(request, 'admin_user/ground_pitches.html', {'pitches': pitches,'grounds':grounds})
    except Exception as e:
        print(e)

def save_edit_pitch(request):
    org_id = request.session["org_id"]
    if request.method == "POST":
        pitch_ids = request.POST.get('pitch_id')
        ground_id = request.POST.get('ground_id')
        pitch_types = request.POST.get('pitch_type')
        size_pitch_square = request.POST.get('size_pitch_square')
        profile_of_pitches_list = request.POST.get('profile_of_pitches')
        last_used_dates = request.POST.get('last_used_date')
        last_used_matches = request.POST.get('last_used_match')
        is_uniformity_of_grasses = 1 if request.POST.get('is_uniformity_of_grass') else 0
        size_of_grasses = request.POST.get('size_of_grass')
        mowing_last_dates = request.POST.get('mowing_last_date')
        mowing_sizes = request.POST.get('mowing_size')
        start_dates_of_pitch_preparation = request.POST.get('start_date_of_pitch_preparation')
        date_pitch_construction = request.POST.get('date_pitch_construction')
        pitch_in_out = request.POST.get('pitch_in_out')
        pitch_placement = request.POST.get('pitch_placement')
        size_pitch = request.POST.get('size_pitch')
        pitch_details = request.POST.get('pitch_details')
        print(pitch_details)

        st=request.POST.get('soil_type')
        if(st=="mixed"):
            soil_types = "mixed="+request.POST.get("soil_type_mixed")
        else:
             soil_types=st

        

        with connection.cursor() as cursor:
                try:
                    cursor.execute(
                        f"""UPDATE {org_id}_pitch_master 
                        SET pitch_type=%s, profile_of_pitches=%s,size_pitch_square=%s, last_used_date=%s, last_used_match=%s, is_uniformtiy_of_grass=%s, 
                            size_of_grass=%s, mowing_last_date=%s, mowing_size=%s,date_pitch_construction=%s, start_date_of_pitch_preparation=%s, soil_type=%s,
                            pitch_in_out=%s,pitch_placement=%s,size_pitch=%s,pitch_details=%s
                        WHERE id=%s and ground_id=%s""",
                        [pitch_types, profile_of_pitches_list,size_pitch_square, last_used_dates, last_used_matches,
                        is_uniformity_of_grasses,
                        size_of_grasses, mowing_last_dates, mowing_sizes,date_pitch_construction, start_dates_of_pitch_preparation,
                        soil_types,pitch_in_out,pitch_placement,size_pitch,pitch_details, pitch_ids,ground_id]
                    )
                except Exception as e:
                    print(e)

        return redirect(f'/usr_admin/ground_pitches/{ground_id}')

def edit_pitch(request,pitch_id,ground_id):
    try:
        org_id = request.session["org_id"]
        with connection.cursor() as cursor:
            cursor.execute(f'SELECT * FROM {org_id}_pitch_master where id=%s',[pitch_id])
            pitch = cursor.fetchall()
        with connection.cursor() as cursor:
            cursor.execute(f'SELECT * FROM {org_id}_ground_master where id=%s',[ground_id])
            ground = cursor.fetchall()

            # print(pitch)
            # print(ground)
        return render(request, 'admin_user/edit_pitch.html', {'pitch': pitch[0],'ground':ground[0]})
    except Exception as e:
        print(e)


def get_cities(request):
    org_id = request.session["org_id"]
    state_id = request.GET.get('state_id')
    with connection.cursor() as cursor:
        cursor.execute(f'''SELECT id, city_name FROM {org_id}_city_master WHERE state_id = %s''', [state_id])
        cities = cursor.fetchall()
    return JsonResponse({'cities': [{'id': city[0], 'name': city[1]} for city in cities]})


def get_grounds(request):
    try:
        org_id = request.session["org_id"]
        # state_id = request.GET.get('state_id')
        
        user_data = request.session.get("user")
        print(user_data)
        grounds=[]
        
        with connection.cursor() as cursor:
            if user_data.get("role")=="admin":
                print("all")
                cursor.execute(f'''SELECT * FROM {org_id}_ground_master WHERE org_id = %s''', [org_id])
                grounds = cursor.fetchall()
                
                
            else:
                print("no all")
                cursor.execute(f'''SELECT * FROM {org_id}_ground_master WHERE org_id = %s and id=%s''', [org_id,user_data.get("ground_id")])
                grounds = cursor.fetchall()
            return JsonResponse({'grounds': [{'ground': ground} for ground in grounds]})
    except Exception as e:
        print(e)

def get_ground(request,ground_id):
    org_id = request.session["org_id"]
    # state_id = request.GET.get('state_id')
    with connection.cursor() as cursor:
        cursor.execute(f'''SELECT * FROM {org_id}_ground_master WHERE org_id = %s and id=%s''', [org_id,ground_id])
        ground = cursor.fetchone()
    return JsonResponse({'ground': ground})

# def get_machinery_details(request,mid):
#     org_id = request.session["org_id"]
#     # state_id = request.GET.get('state_id')
#     with connection.cursor() as cursor:
#         cursor.execute(f'''SELECT * FROM {org_id}_machinery_master WHERE id=%s''', [mid])
#         ground = cursor.fetchone()
#     return JsonResponse({'ground': ground})

# def get_pitches(request,ground_id):
#     org_id = request.session["org_id"]
#     # ground_id = request.session["ground_id"]
#     # state_id = request.GET.get('state_id')
#     with connection.cursor() as cursor:
#         cursor.execute(f'''SELECT * FROM {org_id}_pitch_master WHERE org_id = %s and ground_id=%s order by pitch_no''', [org_id,ground_id])
#         pitches = cursor.fetchall()
#     return JsonResponse({'grounds': [{'pitch': pitch} for pitch in pitches]})

def get_pitches(request, ground_id):
    org_id = request.session["org_id"]

    with connection.cursor() as cursor:
        cursor.execute(f'''
            SELECT p.*, g.city_name 
            FROM {org_id}_pitch_master p
            JOIN {org_id}_ground_master g 
            ON p.ground_id = g.id
            WHERE p.org_id = %s AND p.ground_id = %s
            ORDER BY p.pitch_no
        ''', [org_id, ground_id])

        pitches = cursor.fetchall()

    # JsonResponse में pitch और city दोनों भेजो
    return JsonResponse({
        'grounds': [
            {'pitch': pitch, 'city': pitch[-1]}  # मानते हैं city आखिरी कॉलम में है
            for pitch in pitches
        ]
    })

def get_admin_user_by_org(request):
    org_id = request.session["org_id"]
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT id, name, email, username, address, mobile, org_id, state, city
                FROM super_admin_user_adminuserlist
                WHERE org_id = %s
            """, [org_id])
            rows = cursor.fetchall()
            columns = [col[0] for col in cursor.description]

        # Convert to list of dictionaries
        data = [dict(zip(columns, row)) for row in rows]
        return JsonResponse({"status": "success", "data": data}, safe=False)
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)})

def get_pitch(request,pitch_id):
    org_id = request.session["org_id"]
    # ground_id = request.session["ground_id"]
    # state_id = request.GET.get('state_id')
    with connection.cursor() as cursor:
        cursor.execute(f'''SELECT * FROM {org_id}_pitch_master WHERE org_id = %s and id=%s''', [org_id,pitch_id])
        pitches = cursor.fetchall()
    return JsonResponse({'grounds': [{'pitch': pitch} for pitch in pitches]})

def get_all_pitches(request):
    org_id = request.session["org_id"]
    # ground_id = request.session["ground_id"]
    # state_id = request.GET.get('state_id')
    with connection.cursor() as cursor:
        cursor.execute(f'''SELECT * FROM {org_id}_pitch_master WHERE org_id = %s order by pitch_no''', [org_id])
        pitches = cursor.fetchall()
    return JsonResponse({'grounds': [{'pitches': pitch} for pitch in pitches]})

def curator_daily_recording_form(request):
    try:
        org_id = request.session["org_id"]
        
        pitch_id=0
        ground_id=0
        
        if request.method == "POST":
            rowIndxs=request.POST["rowIndxs"]
            # print(rowIndxs)
            
            rowSplit=rowIndxs.split("-")
            mainIndex=int(rowSplit[0].strip())
            outIndex=int(rowSplit[1].strip())
            pracriceIndex=int(rowSplit[2].strip())
            ppIndex=int(rowSplit[3].strip())
            
            print(mainIndex,outIndex,pracriceIndex,ppIndex)
            maxIndex=max(mainIndex,outIndex,pracriceIndex,ppIndex)
            print("Max Index=",maxIndex)
            
            
            for index in range(1,maxIndex+1):
            
                try:
                    if request.POST.get('pitch_id') != "all":
                        pitch_id = request.POST.get('pitch_id')
                        all_pitches = 0
                    elif request.POST.get('pitch_id') == "all":
                        pitch_id = -1
                        all_pitches = 1
                except:
                    pitch_id=0
                
                
                recording_type = request.POST.get('recording_type')
                try:
                    ground_id = request.POST.get('ground_id')
                except:
                    ground_id=0
                
                pitch_location = request.POST.get('pitch_location')
                rolling_start_date = request.POST.get('rolling_start_date')
                min_temp = request.POST.get('min_temp')
                max_temp = request.POST.get('max_temp')
                forecast = request.POST.get('forecast')
                clagg_hammer = request.POST.get('clagg_hammer')
                moisture = request.POST.get('moisture')

                # print(clagg_hammer)
                # print(moisture)

                # Extract pitch entries
                if(mainIndex>0):
                    machinery_id = ""
                    passes_unit = ""
                    
                    no_of_passes = ""
                    rolling_speed =""
                    last_watering_on = ""
                    quantity_of_water =""
                    time_of_application = ""
                    # last_watering_on = (request.POST.get('last_watering_on'+str(index)) or '').strip() or None
                    # quantity_of_water = (request.POST.get('quantity_of_water'+str(index)) or '').strip() or None
                    # time_of_application = (request.POST.get('time_of_application'+str(index)) or '').strip() or None
                    time_roller =""
                    mover_machine_type =""
                    mover_machinery_name_operator = ""
                    moving_passes_unit ="" 
                    mowing_duration = ""
                    roller_machine_type = ""
                    roller_machinery_name_operator =""
                    is_daily_watering = request.POST.get('is_daily_watering', 'off') == 'on'
                    is_daily_watering = "1" if request.POST.get('is_daily_watering', 'off') == 'on' else "0"
                    mover_machinery_id = ""
                    roller_machine_type = ""
                    
                    
                    # total_records = int(request.POST.get("rolling_entries_json", "0"))
                    watering_entries_json = (request.POST.get("watering_entries_json"+str(index)) or '').strip() or None
                    watering_entries = json.loads(watering_entries_json) if watering_entries_json else []
                    if(len(watering_entries)>0):
                        for water in watering_entries:
                            last_watering_on+=str(water["last_watering_on"])+"__####__"
                            time_of_application+=str(water["time_of_application"])+"__####__"
                            quantity_of_water+=str(water["quantity_of_water"])+"__####__"
                           
                           
                        # print(time_of_application_chemical+"\n"+pitch_main_chemical_weight+"\n"+pitch_main_chemical_unit+"\n"+chemical_details_remark+"\n"+fertilizers_details)
                    else:
                        print("No Watering")
                        
                    rolling_entries_json = (request.POST.get("rolling_entries_json"+str(index)) or '').strip() or None
                    rolling_entries = json.loads(rolling_entries_json) if rolling_entries_json else []
                    if(len(rolling_entries)>0):
                        for roll in rolling_entries:
                            machinery_id+=str(roll["machineryId"])+"__####__"
                            passes_unit+=str(roll["unit"])+"__####__"
                            no_of_passes+=str(roll["passes"])+"__####__"
                            rolling_speed+=str(roll["speed"])+"__####__"
                            time_roller+=str(roll["time"])+"__####__"
                            roller_machine_type+=str(roll["machineType"])+"__####__"
                            roller_machinery_name_operator+=str(roll["operator"])+"__####__"
                            print(machinery_id+" "+passes_unit)
                        # print(time_of_application_chemical+"\n"+pitch_main_chemical_weight+"\n"+pitch_main_chemical_unit+"\n"+chemical_details_remark+"\n"+fertilizers_details)
                    else:
                        print("No Rollers")
                    date_mowing_done_last=""
                    time_of_application_mover=""
                    mowing_done_at_mm=""
                    mover_entries_json = (request.POST.get("mover_entries_json"+str(index)) or '').strip() or None
                    mover_entries = json.loads(mover_entries_json) if mover_entries_json else []
                    if(len(mover_entries)>0):
                        for mov in mover_entries:
                         

                            mover_machinery_id+=str(mov["machineryId"])+"__####__"
                            moving_passes_unit+=str(mov["unit"])+"__####__"
                            mowing_duration+=str(mov["duration"])+"__####__"
                            date_mowing_done_last+=str(mov["date"])+"__####__"
                            time_of_application_mover+=str(mov["time"])+"__####__"
                            mover_machine_type+=str(mov["type"])+"__####__"
                            mover_machinery_name_operator+=str(mov["operator"])+"__####__"
                            mowing_done_at_mm+=str(mov["mowHeight"])+"__####__"
                            print(mover_machinery_id+" "+moving_passes_unit)
                        # print(time_of_application_chemical+"\n"+pitch_main_chemical_weight+"\n"+pitch_main_chemical_unit+"\n"+chemical_details_remark+"\n"+fertilizers_details)
                    else:
                        print("No Movers")
              
                    # date_mowing_done_last = (request.POST.get('date_mowing_done_last'+str(index)) or '').strip() or None
                    # time_of_application_mover = (request.POST.get('time_of_application_mover'+str(index)) or '').strip() or None
                    # mowing_done_at_mm = (request.POST.get('mowing_done_at_mm'+str(index)) or '').strip() or None
                  
                    # is_fertilizers_used = request.POST.get('is_fertilizers_used', 'off') == 'on'
                    is_fertilizers_used =  0
                    # fertilizers_details = (request.POST.get('fertilizers_details'+str(index)) or '').strip() or None
                    fertilizers_details = ""
                    # chemical_details_remark = (request.POST.get('chemical_details_remark'+str(index)) or '').strip() or None
                    chemical_details_remark = ""
                    # time_of_application_chemical = (request.POST.get("time_of_application_chemical"+str(index)) or '').strip() or None
                    time_of_application_chemical = ""
                    # pitch_main_chemical_weight=(request.POST.get("chemical_weight"+str(index)) or '').strip() or None
                    pitch_main_chemical_weight=""
                    # pitch_main_chemical_unit=(request.POST.get("fertilizers_unit"+str(index)) or '').strip() or None
                    pitch_main_chemical_unit=""
                    chemical_entries=(request.POST.get("chemical_entries"+str(index)) or '').strip() or None
                    chemical_entries = json.loads(chemical_entries) if chemical_entries else []
                    if(len(chemical_entries)>0):
                        is_fertilizers_used=1
                        for chem in chemical_entries:
                            time_of_application_chemical+=str(chem["time"])+"__####__"
                            pitch_main_chemical_weight+=str(chem["weight"])+"__####__"
                            pitch_main_chemical_unit+=str(chem["unit"])+"__####__"
                            chemical_details_remark+=str(chem["remark"])+"__####__"
                            fertilizers_details+=str(chem["chemicalId"])+"__####__"
                        # print(time_of_application_chemical+"\n"+pitch_main_chemical_weight+"\n"+pitch_main_chemical_unit+"\n"+chemical_details_remark+"\n"+fertilizers_details)
                    else:
                        is_fertilizers_used=0
                        print("No Chemicals")
                
                else:
                    machinery_id = request.POST.get('machinery_id')
                    no_of_passes = request.POST.get('no_of_passes')
                    rolling_speed = request.POST.get('rolling_speed')
                    last_watering_on = request.POST.get('last_watering_on')
                    quantity_of_water = request.POST.get('quantity_of_water')
                    time_of_application = request.POST.get('time_of_application')
                    time_roller = request.POST.get('time_roller')
                    mover_machine_type = (request.POST.get('mover_machine_type'))
                    mover_machinery_name_operator = (request.POST.get('mover_machinery_name_operator'))
                    moving_passes_unit = (request.POST.get('moving_passes_unit'))
                    mowing_duration = (request.POST.get('mowing_duration'))
                    roller_machine_type = (request.POST.get('roller_machine_type'))
                    roller_machinery_name_operator = (request.POST.get('roller_machinery_name_operator'))
                    # is_daily_watering = request.POST.get('is_daily_watering', 'off') == 'on'
                    # is_daily_watering = "1" if request.POST.get('is_daily_watering', 'off') == 'on' else "0"
                    mover_machinery_id = request.POST.get('mover_machinery_id')
                    date_mowing_done_last = request.POST.get('date_mowing_done_last')
                    time_of_application_mover = request.POST.get('time_of_application_mover')
                    mowing_done_at_mm = request.POST.get('mowing_done_at_mm')
                    # is_fertilizers_used = request.POST.get('is_fertilizers_used', 'off') == 'on'
                    is_fertilizers_used = 1 if request.POST.get('is_fertilizers_used') else 0
                    fertilizers_details = request.POST.get('fertilizers_details')
                    chemical_details_remark = request.POST.get('chemical_details_remark')
                    time_of_application_chemical = request.POST.get("time_of_application_chemical")
                    pitch_main_chemical_weight=request.POST.get("chemical_weight")
                    pitch_main_chemical_unit=request.POST.get("fertilizers_unit")
                    passes_unit=request.POST.get("passes_unit")
                    
                remark_by_groundsman = request.POST.get('remark_by_groundsman')

                # Extract outfield entries
                if(outIndex>0):
                    print("Outfiled1")
                    # out_machinery_id = (request.POST.get('out_machinery_id'+str(index)) or '').strip() or None
                    out_machinery_id = ""
                    out_passes_unit =""
                    print("Outfiled2")
                    
                    # out_no_of_passes = (request.POST.get('out_no_of_passes'+str(index)) or '').strip() or None
                    out_no_of_passes =""
                
                    # out_rolling_speed = (request.POST.get('out_rolling_speed'+str(index)) or '').strip() or None
                    out_rolling_speed =""
                    out_last_watering_on = ""
                    out_quantity_of_water = ""
                    out_time_of_application = ""
                    # out_time_of_application = (request.POST.get('out_time_of_application'+str(index)) or '').strip() or None
                    # out_last_watering_on = (request.POST.get('out_last_watering_on'+str(index)) or '').strip() or None
                    # out_quantity_of_water = (request.POST.get('out_quantity_of_water'+str(index)) or '').strip() or None
                    # # out_time_of_application = (request.POST.get('out_time_of_application'+str(index)) or '').strip() or None
                    # out_time_of_application = (request.POST.get('out_time_of_application'+str(index)) or '').strip() or None
                    # out_time_roller = (request.POST.get('out_time_roller'+str(index)) or '').strip() or None
                    out_time_roller = ""
                    # out_mover_machine_type = (request.POST.get('out_mover_machine_type'+str(index)) or '').strip() or None
                    out_mover_machine_type = ""
                    # out_mover_machinery_name_operator = (request.POST.get('out_mover_machinery_name_operator'+str(index)) or '').strip() or None
                    out_mover_machinery_name_operator = ""
                    # out_moving_passes_unit = (request.POST.get('out_moving_passes_unit'+str(index)) or '').strip() or None
                    out_moving_passes_unit = ""
                    # out_mowing_duration = (request.POST.get('out_mowing_duration'+str(index)) or '').strip() or None
                    out_mowing_duration = ""
                    # out_roller_machine_type = (request.POST.get('out_roller_machine_type'+str(index)) or '').strip() or None
                    out_roller_machine_type =""
                    # out_roller_machinery_name_operator = (request.POST.get('out_roller_machinery_name_operator'+str(index)) or '').strip() or None
                    out_roller_machinery_name_operator = ""
                    # out_is_daily_watering = request.POST.get('out_is_daily_watering', 'off') == 'on'
                    # out_is_daily_watering = "1" if request.POST.get('out_is_daily_watering', 'off') == 'on' else "0"
                    # out_mover_machinery_id = (request.POST.get('out_mover_machinery_id'+str(index)) or '').strip() or None
                    out_mover_machinery_id =""
                    # out_date_mowing_done_last = (request.POST.get('out_date_mowing_done_last'+str(index)) or '').strip() or None
                    out_date_mowing_done_last =""
                    # out_time_of_application_mover = (request.POST.get('out_time_of_application_mover'+str(index)) or '').strip() or None
                    out_time_of_application_mover =""
                    # out_mowing_done_at_mm = (request.POST.get('out_mowing_done_at_mm'+str(index)) or '').strip() or None
                    out_mowing_done_at_mm = ""
                    # out_is_fertilizers_used = request.POST.get('out_is_fertilizers_used', 'off') == 'on'
                    out_is_fertilizers_used =  0
                    # out_fertilizers_details = (request.POST.get('out_fertilizers_details'+str(index)) or '').strip() or None
                    out_fertilizers_details = ""
                    # out_chemical_details_remark = (request.POST.get('out_chemical_details_remark'+str(index)) or '').strip() or None
                    out_chemical_details_remark = ""
                    # out_time_of_application_chemical = (request.POST.get("out_time_of_application_chemical"+str(index)) or '').strip() or None
                    out_time_of_application_chemical = ""
                    # outfield_chemical_weight=(request.POST.get("out_chemical_weight"+str(index)) or '').strip() or None
                    outfield_chemical_weight=""
                    # outfield_chemical_unit=(request.POST.get("out_fertilizers_unit"+str(index)) or '').strip() or None
                    outfield_chemical_unit=""
                    
                    out_watering_entries_json = (request.POST.get("out_watering_entries_json"+str(index)) or '').strip() or None
                    out_watering_entries = json.loads(out_watering_entries_json) if out_watering_entries_json else []
                    if(len(out_watering_entries)>0):
                        for water in out_watering_entries:
                            out_last_watering_on+=str(water["last_watering_on"])+"__####__"
                            out_time_of_application+=str(water["time_of_application"])+"__####__"
                            out_quantity_of_water+=str(water["quantity_of_water"])+"__####__"
                           
                           
                        # print(time_of_application_chemical+"\n"+pitch_main_chemical_weight+"\n"+pitch_main_chemical_unit+"\n"+chemical_details_remark+"\n"+fertilizers_details)
                    else:
                        print("No Watering")
                    
                    out_chemical_entries=(request.POST.get("out_chemical_entries"+str(index)) or '').strip() or None
                    out_chemical_entries = json.loads(out_chemical_entries) if out_chemical_entries else []
                    if(len(out_chemical_entries)>0):
                        out_is_fertilizers_used=1
                        for chem in out_chemical_entries:
                            out_time_of_application_chemical+=str(chem["time"])+"__####__"
                            outfield_chemical_weight+=str(chem["weight"])+"__####__"
                            outfield_chemical_unit+=str(chem["unit"])+"__####__"
                            out_chemical_details_remark+=str(chem["remark"])+"__####__"
                            out_fertilizers_details+=str(chem["chemical"])+"__####__"
                    # print(time_of_application_chemical+"\n"+pitch_main_chemical_weight+"\n"+pitch_main_chemical_unit+"\n"+chemical_details_remark+"\n"+fertilizers_details)
                    else:
                        out_is_fertilizers_used=0
                        print("No Chemicals")
                        print("Outfiled3")
                    
                    out_rolling_entries_json = (request.POST.get("out_rolling_entries_json"+str(index)) or '').strip() or None
                    out_rolling_entries = json.loads(out_rolling_entries_json) if out_rolling_entries_json else []
                    if(len(out_rolling_entries)>0):
                        for roll in out_rolling_entries:
                            out_machinery_id+=str(roll["machineryId"])+"__####__"
                            out_passes_unit+=str(roll["unit"])+"__####__"
                            out_no_of_passes+=str(roll["passes"])+"__####__"
                            out_rolling_speed+=str(roll["speed"])+"__####__"
                            out_time_roller+=str(roll["time"])+"__####__"
                            out_roller_machine_type+=str(roll["machineType"])+"__####__"
                            out_roller_machinery_name_operator+=str(roll["operator"])+"__####__"
                            print(out_machinery_id+" "+out_passes_unit)
                        # print(time_of_application_chemical+"\n"+pitch_main_chemical_weight+"\n"+pitch_main_chemical_unit+"\n"+chemical_details_remark+"\n"+fertilizers_details)
                    else:
                        print("No Rollers")
                    
                    out_mover_entries_json = (request.POST.get("out_mover_entries_json"+str(index)) or '').strip() or None
                    out_mover_entries = json.loads(out_mover_entries_json) if out_mover_entries_json else []
                    if(len(out_mover_entries)>0):
                        for mov in out_mover_entries:
                         

                            out_mover_machinery_id+=str(mov["machineryId"])+"__####__"
                            out_moving_passes_unit+=str(mov["unit"])+"__####__"
                            out_mowing_duration+=str(mov["duration"])+"__####__"
                            out_date_mowing_done_last+=str(mov["date"])+"__####__"
                            out_time_of_application_mover+=str(mov["time"])+"__####__"
                            out_mover_machine_type+=str(mov["type"])+"__####__"
                            out_mover_machinery_name_operator+=str(mov["operator"])+"__####__"
                            out_mowing_done_at_mm+=str(mov["mowHeight"])+"__####__"
                            print(out_mover_machinery_id+" "+out_moving_passes_unit)
                        # print(time_of_application_chemical+"\n"+pitch_main_chemical_weight+"\n"+pitch_main_chemical_unit+"\n"+chemical_details_remark+"\n"+fertilizers_details)
                    else:
                        print("No Movers")
                
                else:
                    out_machinery_id = request.POST.get('out_machinery_id')
                    out_no_of_passes = request.POST.get('out_no_of_passes')
                    out_rolling_speed = request.POST.get('out_rolling_speed')
                    out_last_watering_on = request.POST.get('out_last_watering_on')
                    out_quantity_of_water = request.POST.get('out_quantity_of_water')
                    out_time_of_application = request.POST.get('out_time_of_application')
                    out_time_roller = request.POST.get('out_time_roller')
                    out_mover_machine_type = (request.POST.get('out_mover_machine_type'))
                    out_mover_machinery_name_operator = (request.POST.get('out_mover_machinery_name_operator'))
                    out_moving_passes_unit = (request.POST.get('out_moving_passes_unit'))
                    out_mowing_duration = (request.POST.get('out_mowing_duration'))
                    out_roller_machine_type = (request.POST.get('out_roller_machine_type'))
                    out_roller_machinery_name_operator = (request.POST.get('out_roller_machinery_name_operator'))
                    # out_is_daily_watering = request.POST.get('out_is_daily_watering', 'off') == 'on'
                    # out_is_daily_watering = "1" if request.POST.get('out_is_daily_watering', 'off') == 'on' else "0"
                    out_mover_machinery_id = request.POST.get('out_mover_machinery_id')
                    out_date_mowing_done_last = request.POST.get('out_date_mowing_done_last')
                    out_time_of_application_mover = request.POST.get('out_time_of_application_mover')
                    out_mowing_done_at_mm = request.POST.get('out_mowing_done_at_mm')
                    # out_is_fertilizers_used = request.POST.get('out_is_fertilizers_used', 'off') == 'on'
                    out_is_fertilizers_used = 1 if request.POST.get('out_is_fertilizers_used') else 0
                    out_fertilizers_details = request.POST.get('out_fertilizers_details')
                    out_chemical_details_remark = request.POST.get('out_chemical_details_remark')
                    out_time_of_application_chemical = request.POST.get("out_time_of_application_chemical")
                    outfield_chemical_weight=request.POST.get("out_chemical_weight")
                    outfield_chemical_unit=request.POST.get("out_fertilizers_unit")
                    out_passes_unit=request.POST.get("out_passes_unit")
                    
                out_remark_by_groundsman = request.POST.get('out_remark_by_groundsman')
                  
                
                if(pracriceIndex>0):
                    print("practiceIndex",pracriceIndex)
                    print("index",index)
                    # practice_machinery_id= (request.POST.get("practice_machinery_id"+str(index)) or '').strip() or None
                    practice_machinery_id=""
                    practice_passes_unit =""
                    # practice_passes_unit = (request.POST.get('practice_passes_unit'+str(index)) or '').strip() or None
                    
                    # practice_no_of_passes = (request.POST.get("practice_no_of_passes"+str(index)) or '').strip()+"$##$"+practice_passes_unit  or None
                    practice_no_of_passes = ""
                    
                    practice_rolling_speed = ""
                    # practice_rolling_speed = (request.POST.get("practice_rolling_speed"+str(index)) or '').strip() or None
                    practice_last_watering_on = ""
                    practice_quantity_of_water = ""
                    practice_time_of_application = ""
                    # practice_last_watering_on = (request.POST.get("practice_last_watering_on"+str(index)) or '').strip() or None
                    # practice_quantity_of_water = (request.POST.get("practice_quantity_of_water"+str(index)) or '').strip() or None
                    # practice_time_of_application = (request.POST.get("practice_time_of_application"+str(index)) or '').strip() or None
                    # practice_time_roller = (request.POST.get("practice_time_roller"+str(index)) or '').strip() or None
                    practice_time_roller = ""
                    # practice_mover_machine_type = (request.POST.get('practice_mover_machine_type'+str(index)) or '').strip() or None
                    practice_mover_machine_type = ""
                    # practice_mover_machinery_name_operator = (request.POST.get('practice_mover_machinery_name_operator'+str(index)) or '').strip() or None
                    practice_mover_machinery_name_operator = ""
                    # practice_moving_passes_unit = (request.POST.get('practice_moving_passes_unit'+str(index)) or '').strip() or None
                    practice_moving_passes_unit = ""
                    # practice_mowing_duration = (request.POST.get('practice_mowing_duration'+str(index)) or '').strip() or None
                    practice_mowing_duration = ""
                    # practice_roller_machine_type = (request.POST.get('practice_roller_machine_type'+str(index)) or '').strip() or None
                    practice_roller_machine_type = ""
                    # practice_roller_machinery_name_operator = (request.POST.get('practice_roller_machinery_name_operator'+str(index)) or '').strip() or None
                    practice_roller_machinery_name_operator = ""
                    # practice_mover_machinery_id = (request.POST.get("practice_mover_machinery_id"+str(index)) or '').strip() or None
                    practice_mover_machinery_id = ""
                    # practice_date_mowing_done_last = (request.POST.get("practice_date_mowing_done_last"+str(index)) or '').strip() or None
                    practice_date_mowing_done_last = ""
                    # practice_time_of_application_mover = (request.POST.get("practice_time_of_application_mover"+str(index)) or '').strip() or None
                    time_of_application_practice_mover = ""
                    # practice_mowing_done_at_mm = (request.POST.get("practice_mowing_done_at_mm"+str(index)) or '').strip() or None
                    practice_mowing_done_at_mm = ""
                    practice_is_fertilizers_used =0 
                    # practice_fertilizers_details = (request.POST.get("practice_fertilizers_details"+str(index)) or '').strip() or None
                    practice_fertilizers_details =""
                    practice_chemical_details_remark= ""
                    practice_chemical_details_remark=""
                    # practice_time_of_application_chemical = (request.POST.get("practice_time_of_application_chemical"+str(index)) or '').strip() or None
                    practice_time_of_application_chemical = ""
                    # practice_area_chemical_weight=(request.POST.get("practice_chemical_weight"+str(index)) or '').strip() or None
                    practice_area_chemical_weight=""
                    # practice_area_chemical_unit=(request.POST.get("practice_fertilizers_unit"+str(index)) or '').strip() or None
                    practice_area_chemical_unit=""
                   
                   
                    practice_watering_entries_json = (request.POST.get("practice_watering_entries_json"+str(index)) or '').strip() or None
                    practice_watering_entries = json.loads(practice_watering_entries_json) if practice_watering_entries_json else []
                    if(len(practice_watering_entries)>0):
                        for water in practice_watering_entries:
                            practice_last_watering_on+=str(water["last_watering_on"])+"__####__"
                            practice_time_of_application+=str(water["time_of_application"])+"__####__"
                            practice_quantity_of_water+=str(water["quantity_of_water"])+"__####__"
                           
                           
                        # print(time_of_application_chemical+"\n"+pitch_main_chemical_weight+"\n"+pitch_main_chemical_unit+"\n"+chemical_details_remark+"\n"+fertilizers_details)
                    else:
                        print("No Watering")
                        
                    practice_chemical_entries=(request.POST.get("practice_chemical_entries"+str(index)) or '').strip() or None
                    print("Practice Chemical Entries:",practice_chemical_entries)
                    practice_chemical_entries = json.loads(practice_chemical_entries) if practice_chemical_entries else []
                    if(len(practice_chemical_entries)>0):
                          practice_is_fertilizers_used=1
                          for chem in practice_chemical_entries:
                                practice_time_of_application_chemical+=str(chem["time"])+"__####__"
                                practice_area_chemical_weight+=str(chem["weight"])+"__####__"
                                practice_area_chemical_unit+=str(chem["unit"])+"__####__"
                                practice_chemical_details_remark+=str(chem["remark"])+"__####__"
                                practice_fertilizers_details+=str(chem["chemical"])+"__####__"
                                # print(time_of_application_chemical+"\n"+pitch_main_chemical_weight+"\n"+pitch_main_chemical_unit+"\n"+chemical_details_remark+"\n"+fertilizers_details)
                    else:
                        practice_is_fertilizers_used=0
                        print("No Chemicals")

                    practice_rolling_entries_json = (request.POST.get("practice_rolling_entries_json"+str(index)) or '').strip() or None
                    practice_rolling_entries = json.loads(practice_rolling_entries_json) if practice_rolling_entries_json else []
                    if(len(practice_rolling_entries)>0):
                        for roll in practice_rolling_entries:
                            practice_machinery_id+=str(roll["machineryId"])+"__####__"
                            practice_passes_unit+=str(roll["unit"])+"__####__"
                            practice_no_of_passes+=str(roll["passes"])+"__####__"
                            practice_rolling_speed+=str(roll["speed"])+"__####__"
                            practice_time_roller+=str(roll["time"])+"__####__"
                            practice_roller_machine_type+=str(roll["machineType"])+"__####__"
                            practice_roller_machinery_name_operator+=str(roll["operator"])+"__####__"
                            print(practice_machinery_id+" "+practice_passes_unit)
                        # print(time_of_application_chemical+"\n"+pitch_main_chemical_weight+"\n"+pitch_main_chemical_unit+"\n"+chemical_details_remark+"\n"+fertilizers_details)
                    else:
                        print("No Rollers")
                    
                    practice_mover_entries_json = (request.POST.get("practice_mover_entries_json"+str(index)) or '').strip() or None
                    practice_mover_entries = json.loads(practice_mover_entries_json) if practice_mover_entries_json else []
                    if(len(practice_mover_entries)>0):
                        for mov in practice_mover_entries:
                            practice_mover_machinery_id+=str(mov["machineryId"])+"__####__"
                            practice_moving_passes_unit+=str(mov["unit"])+"__####__"
                            practice_mowing_duration+=str(mov["duration"])+"__####__"
                            practice_date_mowing_done_last+=str(mov["date"])+"__####__"
                            time_of_application_practice_mover+=str(mov["time"])+"__####__"
                            practice_mover_machine_type+=str(mov["type"])+"__####__"
                            practice_mover_machinery_name_operator+=str(mov["operator"])+"__####__"
                            practice_mowing_done_at_mm+=str(mov["mowHeight"])+"__####__"
                            print(practice_mover_machinery_id+" "+practice_moving_passes_unit)
                        # print(time_of_application_chemical+"\n"+pitch_main_chemical_weight+"\n"+pitch_main_chemical_unit+"\n"+chemical_details_remark+"\n"+fertilizers_details)
                    else:
                        print("No Movers")
                    
                else:
                    print("Practice1 0 hai")
                    practice_machinery_id= request.POST.get("practice_machinery_id")
                    practice_no_of_passes = request.POST.get("practice_no_of_passes")
                    practice_rolling_speed = request.POST.get("practice_rolling_speed")
                    practice_last_watering_on = request.POST.get("practice_last_watering_on")
                    practice_quantity_of_water = request.POST.get("practice_quantity_of_water")
                    practice_time_of_application = request.POST.get("practice_time_of_application")
                    practice_time_roller = request.POST.get("practice_time_roller")
                    practice_mover_machine_type = (request.POST.get('practice_mover_machine_type'))
                    practice_mover_machinery_name_operator = (request.POST.get('practice_mover_machinery_name_operator'))
                    practice_moving_passes_unit = (request.POST.get('practice_moving_passes_unit'))
                    practice_mowing_duration = (request.POST.get('practice_mowing_duration'))
                    practice_roller_machine_type = (request.POST.get('practice_roller_machine_type'))
                    practice_roller_machinery_name_operator = (request.POST.get('practice_roller_machinery_name_operator'))
                    practice_mover_machinery_id = request.POST.get("practice_mover_machinery_id")
                    practice_date_mowing_done_last = request.POST.get("practice_date_mowing_done_last")
                    time_of_application_practice_mover = request.POST.get("practice_time_of_application_mover")
                    practice_mowing_done_at_mm = request.POST.get("practice_mowing_done_at_mm")
                    practice_is_fertilizers_used =1 if request.POST.get('practice_is_fertilizers_used') else 0 
                    practice_fertilizers_details = request.POST.get("practice_fertilizers_details")
                    practice_chemical_details_remark= request.POST.get("practice_chemical_details_remark")
                    practice_time_of_application_chemical = request.POST.get("practice_time_of_application_chemical")
                    practice_area_chemical_weight=request.POST.get("practice_chemical_weight")
                    practice_area_chemical_unit=request.POST.get("practice_fertilizers_unit")
                    practice_passes_unit=request.POST.get("practice_passes_unit")

                practice_remark_by_groundsman = request.POST.get("practice_remark_by_groundsman")
                
                pitch_main =  1 if request.POST.get('pitch-main') else 0
                pitch_practice =  1 if request.POST.get('pitch-practice') else 0
                outfield =  1 if request.POST.get('outfield') else 0
                practice_area =  1 if request.POST.get('practice-area') else 0
                
                if(ppIndex>0):
                    print("pp main hai")
                    # pp_machinery_id = (request.POST.get("pp_machinery_id"+str(index)) or '').strip() or None
                    pp_machinery_id =""
                    # pp_passes_unit = (request.POST.get('pp_passes_unit'+str(index)) or '').strip() or None
                    pp_passes_unit =""
                    
                    # pp_no_of_passes = (request.POST.get("pp_no_of_passes"+str(index)) or '').strip()+"$##$"+pp_passes_unit  or None
                    pp_no_of_passes = ""
                    
                    pp_rolling_speed = ""
                    # pp_rolling_speed = (request.POST.get("pp_rolling_speed"+str(index)) or '').strip() or None
                    pp_last_watering_on = ""
                    pp_quantity_of_water = ""
                    pp_time_of_application =""
                    # pp_last_watering_on = (request.POST.get("pp_last_watering_on"+str(index)) or '').strip() or None
                    # pp_quantity_of_water = (request.POST.get("pp_quantity_of_water"+str(index)) or '').strip() or None
                    # pp_time_of_application = (request.POST.get("pp_time_of_application"+str(index)) or '').strip() or None
                    # pp_time_roller = (request.POST.get("pp_time_roller"+str(index)) or '').strip() or None
                    pp_time_roller =""
                    # pp_mover_machine_type = (request.POST.get('pp_mover_machine_type'+str(index)) or '').strip() or None
                    pp_mover_machine_type = ""
                    pp_mover_machinery_name_operator =""
                    # pp_mover_machinery_name_operator = (request.POST.get('pp_mover_machinery_name_operator'+str(index)) or '').strip() or None
                    # pp_moving_passes_unit = (request.POST.get('pp_moving_passes_unit'+str(index)) or '').strip() or None
                    pp_moving_passes_unit = ""
                    # pp_mowing_duration = (request.POST.get('pp_mowing_duration'+str(index)) or '').strip() or None
                    pp_mowing_duration = ""
                    # pp_roller_machine_type = (request.POST.get('pp_roller_machine_type'+str(index)) or '').strip() or None
                    pp_roller_machine_type = ""
                    # pp_roller_machinery_name_operator = (request.POST.get('pp_roller_machinery_name_operator'+str(index)) or '').strip() or None
                    pp_roller_machinery_name_operator = ""
                    # pp_mover_machinery_id = (request.POST.get("pp_mover_machinery_id"+str(index)) or '').strip() or None
                    pp_mover_machinery_id = ""
                    # pp_date_mowing_done_last = (request.POST.get("pp_date_mowing_done_last"+str(index)) or '').strip() or None
                    pp_date_mowing_done_last =""
                    # pp_time_of_application_mover = (request.POST.get("pp_time_of_application_mover"+str(index)) or '').strip() or None
                    pp_time_of_application_mover = ""
                    # pp_mowing_done_at_mm = (request.POST.get("pp_mowing_done_at_mm"+str(index)) or '').strip() or None
                    pp_mowing_done_at_mm =""
                    pp_is_fertilizers_used =  0
                    # pp_fertilizers_details = (request.POST.get("pp_fertilizers_details"+str(index)) or '').strip() or None
                    pp_fertilizers_details =""
                    # pp_chemical_details_remark = (request.POST.get("pp_chemical_details_remark"+str(index)) or '').strip() or None
                    pp_chemical_details_remark =""
                    pp_time_of_application_chemical = ""
                    # pitch_practice_chemical_weight=(request.POST.get("pp_chemical_weight"+str(index)) or '').strip() or None
                    pitch_practice_chemical_weight=""
                    # pitch_practice_chemical_unit=(request.POST.get("pp_fertilizers_unit"+str(index)) or '').strip() or None
                    pitch_practice_chemical_unit=""
                   
                    pp_watering_entries_json = (request.POST.get("pp_watering_entries_json"+str(index)) or '').strip() or None
                    pp_watering_entries = json.loads(pp_watering_entries_json) if pp_watering_entries_json else []
                    if(len(pp_watering_entries)>0):
                        for water in pp_watering_entries:
                            pp_last_watering_on+=str(water["last_watering_on"])+"__####__"
                            pp_time_of_application+=str(water["time_of_application"])+"__####__"
                            pp_quantity_of_water+=str(water["quantity_of_water"])+"__####__"
                           
                           
                        # print(time_of_application_chemical+"\n"+pitch_main_chemical_weight+"\n"+pitch_main_chemical_unit+"\n"+chemical_details_remark+"\n"+fertilizers_details)
                    else:
                        print("No Watering")
                   
                    pp_chemical_entries=(request.POST.get("pp_chemical_entries"+str(index)) or '').strip() or None
                    pp_chemical_entries = json.loads(pp_chemical_entries) if pp_chemical_entries else []
                    if(len(pp_chemical_entries)>0):
                        print("PP Chemical Entries 1:",pp_chemical_entries)
                        pp_is_fertilizers_used=1
                        for chem in pp_chemical_entries:
                            print("PP Chemical Entries 2:",pp_chemical_entries)
                            pp_time_of_application_chemical+=str(chem["time"])+"__####__"
                            print("PP Chemical Entries 3:",pp_chemical_entries)
                            pitch_practice_chemical_weight+=str(chem["weight"])+"__####__"
                            print("PP Chemical Entries 4:",pp_chemical_entries)
                            pitch_practice_chemical_unit+=str(chem["unit"])+"__####__"
                            print("PP Chemical Entries 5:",pp_chemical_entries)
                            pp_chemical_details_remark+=str(chem["remark"])+"__####__"
                            print("PP Chemical Entries 6:",pp_chemical_entries)
                            pp_fertilizers_details+=str(chem["chem"])+"__####__"
                            print("PP Chemical Entries 7:",pp_chemical_entries)
                            # print(time_of_application_chemical+"\n"+pitch_main_chemical_weight+"\n"+pitch_main_chemical_unit+"\n"+chemical_details_remark+"\n"+fertilizers_details)
                    else:
                        pp_is_fertilizers_used=0
                        print("No Chemicals")
                        
                   
                    
                    pp_rolling_entries_json = (request.POST.get("pp_rolling_entries_json"+str(index)) or '').strip() or None
                    pp_rolling_entries = json.loads(pp_rolling_entries_json) if pp_rolling_entries_json else []
                    print("PP Rolling Entries:",pp_rolling_entries)
                    if(len(pp_rolling_entries)>0):
                        for roll in pp_rolling_entries:
                            pp_machinery_id+=str(roll["machineryId"])+"__####__"
                            pp_passes_unit+=str(roll["unit"])+"__####__"
                            pp_no_of_passes+=str(roll["passes"])+"__####__"
                            pp_rolling_speed+=str(roll["speed"])+"__####__"
                            pp_time_roller+=str(roll["time"])+"__####__"
                            pp_roller_machine_type+=str(roll["machineType"])+"__####__"
                            pp_roller_machinery_name_operator+=str(roll["operator"])+"__####__"
                            print(pp_machinery_id+" "+pp_passes_unit)
                        # print(time_of_application_chemical+"\n"+pitch_main_chemical_weight+"\n"+pitch_main_chemical_unit+"\n"+chemical_details_remark+"\n"+fertilizers_details)
                    else:
                        print("No Rollers")
                    
                    pp_mover_entries_json = (request.POST.get("pp_mover_entries_json"+str(index)) or '').strip() or None
                    pp_mover_entries = json.loads(pp_mover_entries_json) if pp_mover_entries_json else []
                    print("PP Mover Entries:",pp_mover_entries)
                    if(len(pp_mover_entries)>0):
                        for mov in pp_mover_entries:
                         

                            pp_mover_machinery_id+=str(mov["machineryId"])+"__####__"
                            pp_moving_passes_unit+=str(mov["unit"])+"__####__"
                            pp_mowing_duration+=str(mov["duration"])+"__####__"
                            pp_date_mowing_done_last+=str(mov["date"])+"__####__"
                            pp_time_of_application_mover+=str(mov["time"])+"__####__"
                            pp_mover_machine_type+=str(mov["type"])+"__####__"
                            pp_mover_machinery_name_operator+=str(mov["operator"])+"__####__"
                            pp_mowing_done_at_mm+=str(mov["mowHeight"])+"__####__"
                            print(pp_mover_machinery_id+" "+pp_moving_passes_unit)
                        # print(time_of_application_chemical+"\n"+pitch_main_chemical_weight+"\n"+pitch_main_chemical_unit+"\n"+chemical_details_remark+"\n"+fertilizers_details)
                    else:
                        print("No Movers")
                    
                else:
                    pp_machinery_id = request.POST.get("pp_machinery_id")
                    pp_no_of_passes = request.POST.get("pp_no_of_passes")
                    pp_rolling_speed = request.POST.get("pp_rolling_speed")
                    pp_last_watering_on = request.POST.get("pp_last_watering_on")
                    pp_quantity_of_water = request.POST.get("pp_quantity_of_water")
                    pp_time_of_application = request.POST.get("pp_time_of_application")
                    pp_time_roller = request.POST.get("pp_time_roller")
                    pp_mover_machine_type = (request.POST.get('pp_mover_machine_type'))
                    pp_mover_machinery_name_operator = (request.POST.get('pp_mover_machinery_name_operator'))
                    pp_moving_passes_unit = (request.POST.get('pp_moving_passes_unit'))
                    pp_mowing_duration = (request.POST.get('pp_mowing_duration'))
                    pp_roller_machine_type = (request.POST.get('pp_roller_machine_type'))
                    pp_roller_machinery_name_operator = (request.POST.get('pp_roller_machinery_name_operator'))
                    pp_mover_machinery_id = request.POST.get("pp_mover_machinery_id")
                    pp_date_mowing_done_last = request.POST.get("pp_date_mowing_done_last")
                    pp_time_of_application_mover = request.POST.get("pp_time_of_application_mover")
                    pp_mowing_done_at_mm = request.POST.get("pp_mowing_done_at_mm")
                    pp_is_fertilizers_used = 1 if request.POST.get('pp_is_fertilizers_used') else 0
                    pp_fertilizers_details = request.POST.get("pp_fertilizers_details")
                    pp_chemical_details_remark = request.POST.get("pp_chemical_details_remark")
                    pp_time_of_application_chemical = request.POST.get("pp_time_of_application_chemical")
                    pitch_practice_chemical_weight=request.POST.get("pp_chemical_weight")
                    pitch_practice_chemical_unit=request.POST.get("pp_fertilizers_unit")
                    pp_passes_unit=request.POST.get("practice_passes_unit")
                    
                pp_remark_by_groundsman = request.POST.get("pp_remark_by_groundsman")

                # Insert data into the database
                with connection.cursor() as cursor:
                    query = f"""
                        INSERT INTO {org_id}_curator_daily_recording_master (
                            pitch_id,recording_type, ground_id, pitch_location,
                            rolling_start_date, min_temp, max_temp, forecast, 
                            clagg_hammer, moisture,  machinery_id, no_of_passes, 
                            rolling_speed, last_watering_on, quantity_of_water, time_of_application,
                            time_roller,out_time_roller, mover_machinery_id, date_mowing_done_last,
                            time_of_application_mover, mowing_done_at_mm,  is_fertilizers_used, fertilizers_details, 
                            chemical_details_remark, remark_by_groundsman,  out_machinery_id, out_no_of_passes,
                            out_rolling_speed, out_last_watering_on, out_quantity_of_water, out_time_of_application,
                            out_mover_machinery_id, out_date_mowing_done_last, time_of_application_out_mover, out_mowing_done_at_mm,
                            out_is_fertilizers_used, out_fertilizers_details,  out_chemical_details_remark, out_remark_by_groundsman,   practice_machinery_id ,
                            practice_no_of_passes ,
                            practice_rolling_speed ,
                            practice_last_watering_on,
                            practice_quantity_of_water ,
                            practice_time_of_application ,
                            practice_time_roller ,

                            practice_mover_machinery_id ,
                            practice_date_mowing_done_last ,
                            time_of_application_practice_mover ,
                            practice_mowing_done_at_mm ,
                            practice_is_fertilizers_used ,
                            practice_fertilizers_details ,
                            practice_chemical_details_remark,
                            practice_remark_by_groundsman,
                            time_of_application_chemical,
                            out_time_of_application_chemical,
                            practice_time_of_application_chemical,
                            pitch_main, pitch_practice, outfield, practice_area,
                            
                            pp_machinery_id, pp_no_of_passes, pp_rolling_speed, pp_last_watering_on,
                            pp_quantity_of_water, pp_time_of_application, pp_time_roller, pp_mover_machinery_id,
                            pp_date_mowing_done_last, pp_time_of_application_mover, pp_mowing_done_at_mm, pp_is_fertilizers_used,
                            pp_fertilizers_details, pp_chemical_details_remark, pp_remark_by_groundsman, pp_time_of_application_chemical,
                            pitch_main_chemical_weight,pitch_practice_chemical_weight,outfield_chemical_weight,practice_area_chemical_weight,
                            pitch_main_chemical_unit,pitch_practice_chemical_unit,outfield_chemical_unit,practice_area_chemical_unit,
                            pp_mover_machine_type, pp_mover_machinery_name_operator , pp_moving_passes_unit ,
                            pp_mowing_duration ,practice_mover_machine_type , practice_mover_machinery_name_operator ,
                            practice_moving_passes_unit ,practice_mowing_duration, out_mover_machine_type ,
                            out_mover_machinery_name_operator, out_moving_passes_unit ,out_mowing_duration ,
                            mover_machine_type , mover_machinery_name_operator ,moving_passes_unit, mowing_duration,
                            roller_machine_type,
                            roller_machinery_name_operator,
                            pp_roller_machine_type,
                            pp_roller_machinery_name_operator,
                            out_roller_machine_type,
                            out_roller_machinery_name_operator,
                            practice_roller_machine_type,
                            practice_roller_machinery_name_operator,
                            passes_unit,
                            out_passes_unit,
                            pp_passes_unit,
                            practice_passes_unit

                            ) 
                            
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
                                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
                                    %s, %s, %s, %s, %s, %s,%s,%s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s, %s,%s, %s, %s, %s,%s, %s, %s,
                        %s, %s, %s, %s,%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
                        %s, %s, %s, %s, %s, %s, %s, %s,%s, %s, %s, %s, %s, %s, %s, %s,%s, %s, %s, %s, %s, %s, %s, %s,%s, %s, %s, %s,%s, %s, %s, %s,%s, %s, %s,%s)
                            """
                    values = [
                        pitch_id, recording_type, ground_id,pitch_location, rolling_start_date, min_temp, max_temp, forecast, clagg_hammer, moisture,
                        machinery_id, no_of_passes, rolling_speed, last_watering_on, quantity_of_water, time_of_application,time_roller,out_time_roller,
                        mover_machinery_id, date_mowing_done_last, time_of_application_mover,
                        mowing_done_at_mm,
                        is_fertilizers_used, fertilizers_details, chemical_details_remark, remark_by_groundsman,
                        out_machinery_id, out_no_of_passes, out_rolling_speed, out_last_watering_on, out_quantity_of_water,
                        out_time_of_application, out_mover_machinery_id, out_date_mowing_done_last,
                        out_time_of_application_mover, out_mowing_done_at_mm, out_is_fertilizers_used,
                        out_fertilizers_details,
                        out_chemical_details_remark, out_remark_by_groundsman, 

                        practice_machinery_id ,
                        practice_no_of_passes ,
                        practice_rolling_speed ,
                        practice_last_watering_on,
                        practice_quantity_of_water ,
                        practice_time_of_application ,
                        practice_time_roller,
                        practice_mover_machinery_id ,
                        practice_date_mowing_done_last ,
                        time_of_application_practice_mover,
                        practice_mowing_done_at_mm ,
                        practice_is_fertilizers_used ,
                        practice_fertilizers_details ,
                        practice_chemical_details_remark,
                        practice_remark_by_groundsman,

                        time_of_application_chemical,
                        out_time_of_application_chemical,
                        practice_time_of_application_chemical,
                        pitch_main, pitch_practice, outfield, practice_area,
                        pp_machinery_id, pp_no_of_passes, pp_rolling_speed, pp_last_watering_on,
                            pp_quantity_of_water, pp_time_of_application, pp_time_roller, pp_mover_machinery_id,
                            pp_date_mowing_done_last, pp_time_of_application_mover, pp_mowing_done_at_mm, pp_is_fertilizers_used,
                            pp_fertilizers_details, pp_chemical_details_remark, pp_remark_by_groundsman, pp_time_of_application_chemical,
                        pitch_main_chemical_weight, pitch_practice_chemical_weight, outfield_chemical_weight,practice_area_chemical_weight,
                        pitch_main_chemical_unit, pitch_practice_chemical_unit, outfield_chemical_unit, practice_area_chemical_unit,
                         pp_mover_machine_type, pp_mover_machinery_name_operator , pp_moving_passes_unit ,
                            pp_mowing_duration ,practice_mover_machine_type , practice_mover_machinery_name_operator ,
                            practice_moving_passes_unit ,practice_mowing_duration, out_mover_machine_type ,
                            out_mover_machinery_name_operator, out_moving_passes_unit ,out_mowing_duration ,
                            mover_machine_type , mover_machinery_name_operator ,moving_passes_unit, mowing_duration,
                             roller_machine_type,roller_machinery_name_operator,pp_roller_machine_type,
                        pp_roller_machinery_name_operator, out_roller_machine_type,out_roller_machinery_name_operator,
                        practice_roller_machine_type, practice_roller_machinery_name_operator, passes_unit,
                        out_passes_unit,
                        pp_passes_unit,
                        practice_passes_unit


                    ]

                    # Debugging: Print the query and values
                    # print("Query:", query)
                    # print("Values:", values)

                    cursor.execute(query, values)
                    
                    
                    # print("Hello")
            return redirect('curator_daily_recording_list')


        with connection.cursor() as cursor:
            cursor.execute(f"SELECT * FROM {org_id}_pitch_master")
            pitches = cursor.fetchall()
            # print(pitches)

        return render(request, 'admin_user/curator_daily_recording_form.html', {'pitches': pitches})
    except Exception as e:
        print(e)

def update_daily(request,daily_id):
    try:
        org_id = request.session["org_id"]
       
        with connection.cursor() as cursor:
            cursor.execute(f'SELECT * FROM {org_id}_curator_daily_recording_master WHERE id = %s', [daily_id])
            dailyRecord = cursor.fetchone()
            # print(dailyRecord)

        if not dailyRecord:
            raise Exception("dailyRecord not found")
        if request.method == "POST":

            if request.POST.get('pitch_id_text') != "all":
                pitch_id_text = request.POST.get('pitch_id_text')
                all_pitches = 0
            elif request.POST.get('pitch_id_text') == "all":
                pitch_id_text = -1
                all_pitches = 1

         
            id = request.POST.get('id')
            recording_type = request.POST.get('recording_type')
            # ground_id = request.POST.get('ground_id')
            # pitch_id = request.POST.get('pitch_id')
            pitch_location = request.POST.get('pitch_location')
            rolling_start_date = request.POST.get('rolling_start_date')
            min_temp = request.POST.get('min_temp')
            max_temp = request.POST.get('max_temp')
            forecast = request.POST.get('forecast')
            
            clagg_hammer = request.POST.get('clagg_hammer')
            moisture = request.POST.get('moisture')
            # Extract pitch entries
            pitch_id_text = request.POST.get('pitch_id_text')
            ground_id_text = request.POST.get('ground_id_text')
            # print(pitch_id_text,ground_id_text)
            machinery_id = ""
            no_of_passes = ""
            rolling_speed = ""
            last_watering_on = request.POST.get('last_watering_on')
            quantity_of_water = request.POST.get('quantity_of_water')
            time_of_application = request.POST.get('time_of_application')
            time_roller = ""
            # is_daily_watering = request.POST.get('is_daily_watering', 'off') == 'on'
            # is_daily_watering = "1" if request.POST.get('is_daily_watering', 'off') == 'on' else "0"
            mover_machinery_id = ""
            date_mowing_done_last = ""
            time_of_application_mover = ""
            mowing_done_at_mm = ""
            # is_fertilizers_used = request.POST.get('is_fertilizers_used', 'off') == 'on'
            is_fertilizers_used = 0
            fertilizers_details = ""
            chemical_details_remark = ""
            remark_by_groundsman = ""
            time_of_application_chemical = ""
            out_time_of_application_chemical = ""
            practice_time_of_application_chemical = ""
            
            #main
            passes_unit = ""
            roller_machine_type = ""
            roller_machinery_name_operator =""
            mover_machine_type =""
            mover_machinery_name_operator = ""
            moving_passes_unit ="" 
            mowing_duration = ""
            
            #outfield
            out_passes_unit =""
            out_mover_machine_type = ""
            out_mover_machinery_name_operator = ""
            out_moving_passes_unit = ""
            out_mowing_duration = ""
            out_roller_machine_type =""
            out_roller_machinery_name_operator = ""
            
            
            #practice
            practice_passes_unit =""
            practice_mover_machine_type = ""
            practice_mover_machinery_name_operator = ""
            practice_moving_passes_unit = ""
            practice_mowing_duration = ""
            practice_roller_machine_type = ""
            practice_roller_machinery_name_operator = ""
            
            #pp
            pp_passes_unit =""
            pp_mover_machine_type = ""
            pp_mover_machinery_name_operator =""
            pp_moving_passes_unit = ""
            pp_mowing_duration = ""
            pp_roller_machine_type = ""
            pp_roller_machinery_name_operator = ""
            
            pitch_main_chemical_weight=""
            pitch_main_chemical_unit=""
            
            outfield_chemical_weight=""
            outfield_chemical_unit=""
            
            practice_area_chemical_weight=""
            practice_area_chemical_unit=""
            
            pitch_practice_chemical_weight=""
            pitch_practice_chemical_unit=""
            
            
            
            rolling_entries_json = (request.POST.get("rolling_entries_json") or '').strip() or None
            rolling_entries = json.loads(rolling_entries_json) if rolling_entries_json else []
            if(len(rolling_entries)>0):
                for roll in rolling_entries:
                    machinery_id+=str(roll["machineryId"])+"__####__"
                    passes_unit+=str(roll["unit"])+"__####__"
                    no_of_passes+=str(roll["passes"])+"__####__"
                    rolling_speed+=str(roll["speed"])+"__####__"
                    time_roller+=str(roll["time"])+"__####__"
                    roller_machine_type+=str(roll["machineType"])+"__####__"
                    roller_machinery_name_operator+=str(roll["operator"])+"__####__"
                    print("main",machinery_id+" "+passes_unit)
                    # print(time_of_application_chemical+"\n"+pitch_main_chemical_weight+"\n"+pitch_main_chemical_unit+"\n"+chemical_details_remark+"\n"+fertilizers_details)
            else:
                print("No Rollers")
                
            mover_entries_json = (request.POST.get("mover_entries_json") or '').strip() or None
            mover_entries = json.loads(mover_entries_json) if mover_entries_json else []
            if(len(mover_entries)>0):
                for mov in mover_entries:
                    mover_machinery_id+=str(mov["machineryId"])+"__####__"
                    moving_passes_unit+=str(mov["unit"])+"__####__"
                    mowing_duration+=str(mov["duration"])+"__####__"
                    date_mowing_done_last+=str(mov["date"])+"__####__"
                    time_of_application_mover+=str(mov["time"])+"__####__"
                    mover_machine_type+=str(mov["type"])+"__####__"
                    mover_machinery_name_operator+=str(mov["operator"])+"__####__"
                    mowing_done_at_mm+=str(mov["mowHeight"])+"__####__"
                    print(mover_machinery_id+" "+moving_passes_unit)
                    # print(time_of_application_chemical+"\n"+pitch_main_chemical_weight+"\n"+pitch_main_chemical_unit+"\n"+chemical_details_remark+"\n"+fertilizers_details)
            else:
                print("No Movers")
            
            chemical_entries=(request.POST.get("chemical_entries") or '').strip() or None
            chemical_entries = json.loads(chemical_entries) if chemical_entries else []
            if(len(chemical_entries)>0):
                is_fertilizers_used=1
                for chem in chemical_entries:
                    time_of_application_chemical+=str(chem["time"])+"__####__"
                    pitch_main_chemical_weight+=str(chem["weight"])+"__####__"
                    pitch_main_chemical_unit+=str(chem["unit"])+"__####__"
                    chemical_details_remark+=str(chem["remark"])+"__####__"
                    fertilizers_details+=str(chem["chem"])+"__####__"
                    # print(time_of_application_chemical+"\n"+pitch_main_chemical_weight+"\n"+pitch_main_chemical_unit+"\n"+chemical_details_remark+"\n"+fertilizers_details)
            else:
                is_fertilizers_used=0
                print("No Chemicals")
                
            pp_machinery_id = ""
            pp_no_of_passes = ""
            pp_rolling_speed = ""
            pp_last_watering_on = request.POST.get('pp_last_watering_on')
            pp_quantity_of_water = request.POST.get('pp_quantity_of_water')
            pp_time_of_application = request.POST.get('pp_time_of_application')
            pp_time_roller = ""
            pp_mover_machinery_id = ""
            pp_date_mowing_done_last = ""
            pp_time_of_application_mover = ""
            pp_mowing_done_at_mm = ""
            pp_is_fertilizers_used = 0
            pp_fertilizers_details = ""
            pp_chemical_details_remark = ""
            pp_remark_by_groundsman = ""
            pp_time_of_application_chemical = ""
            print("time")
            pp_chemical_entries=(request.POST.get("pp_chemical_entries") or '').strip() or None
            pp_chemical_entries = json.loads(pp_chemical_entries) if pp_chemical_entries else []
            if(len(pp_chemical_entries)>0):
                pp_is_fertilizers_used=1
                for chem in pp_chemical_entries:
                    pp_time_of_application_chemical+=str(chem["time"])+"__####__"
                    pitch_practice_chemical_weight+=str(chem["weight"])+"__####__"
                    pitch_practice_chemical_unit+=str(chem["unit"])+"__####__"
                    pp_chemical_details_remark+=str(chem["remark"])+"__####__"
                    pp_fertilizers_details+=str(chem["chem"])+"__####__"
                    # print(time_of_application_chemical+"\n"+pitch_main_chemical_weight+"\n"+pitch_main_chemical_unit+"\n"+chemical_details_remark+"\n"+fertilizers_details)
            else:
                pp_is_fertilizers_used=0
                print("No Chemicals")
                        
                   
                    
            pp_rolling_entries_json = (request.POST.get("pp_rolling_entries_json") or '').strip() or None
            pp_rolling_entries = json.loads(pp_rolling_entries_json) if pp_rolling_entries_json else []
            if(len(pp_rolling_entries)>0):
                for roll in pp_rolling_entries:
                    pp_machinery_id+=str(roll["machineryId"])+"__####__"
                    pp_passes_unit+=str(roll["unit"])+"__####__"
                    pp_no_of_passes+=str(roll["passes"])+"__####__"
                    pp_rolling_speed+=str(roll["speed"])+"__####__"
                    pp_time_roller+=str(roll["time"])+"__####__"
                    pp_roller_machine_type+=str(roll["machineType"])+"__####__"
                    pp_roller_machinery_name_operator+=str(roll["operator"])+"__####__"
                    print(pp_machinery_id+" "+pp_passes_unit)
                    # print(time_of_application_chemical+"\n"+pitch_main_chemical_weight+"\n"+pitch_main_chemical_unit+"\n"+chemical_details_remark+"\n"+fertilizers_details)
            else:
                print("No Rollers")
                    
            pp_mover_entries_json = (request.POST.get("pp_mover_entries_json") or '').strip() or None
            pp_mover_entries = json.loads(pp_mover_entries_json) if pp_mover_entries_json else []
            if(len(pp_mover_entries)>0):
                for mov in pp_mover_entries:         
                    pp_mover_machinery_id+=str(mov["machineryId"])+"__####__"
                    pp_moving_passes_unit+=str(mov["unit"])+"__####__"
                    pp_mowing_duration+=str(mov["duration"])+"__####__"
                    pp_date_mowing_done_last+=str(mov["date"])+"__####__"
                    pp_time_of_application_mover+=str(mov["time"])+"__####__"
                    pp_mover_machine_type+=str(mov["type"])+"__####__"
                    pp_mover_machinery_name_operator+=str(mov["operator"])+"__####__"
                    pp_mowing_done_at_mm+=str(mov["mowHeight"])+"__####__"
                    print("pp ",pp_mover_machinery_id+" "+pp_moving_passes_unit)
                    # print(time_of_application_chemical+"\n"+pitch_main_chemical_weight+"\n"+pitch_main_chemical_unit+"\n"+chemical_details_remark+"\n"+fertilizers_details)
            else:
                print("No Movers")
            
            
            out_machinery_id = ""
            out_no_of_passes = ""
            out_rolling_speed = ""
            out_last_watering_on = request.POST.get('out_last_watering_on')
            out_quantity_of_water = request.POST.get('out_quantity_of_water')
            out_time_of_application = request.POST.get('out_time_of_application')
           
            out_time_roller = ""
            # out_is_daily_watering = request.POST.get('out_is_daily_watering', 'off') == 'on'
            # out_is_daily_watering = "1" if request.POST.get('out_is_daily_watering', 'off') == 'on' else "0"
            out_mover_machinery_id = ""
            out_date_mowing_done_last = ""
            out_time_of_application_mover = ""
            out_mowing_done_at_mm = ""
            # out_is_fertilizers_used = request.POST.get('out_is_fertilizers_used', 'off') == 'on'
            out_is_fertilizers_used =  0
            out_fertilizers_details = ""
            out_chemical_details_remark = ""
            out_remark_by_groundsman = ""
            
            out_rolling_entries_json = (request.POST.get("out_rolling_entries_json") or '').strip() or None
            out_rolling_entries = json.loads(out_rolling_entries_json) if out_rolling_entries_json else []
            if(len(out_rolling_entries)>0):
                for roll in out_rolling_entries:
                    out_machinery_id+=str(roll["machineryId"])+"__####__"
                    out_passes_unit+=str(roll["unit"])+"__####__"
                    out_no_of_passes+=str(roll["passes"])+"__####__"
                    out_rolling_speed+=str(roll["speed"])+"__####__"
                    out_time_roller+=str(roll["time"])+"__####__"
                    out_roller_machine_type+=str(roll["machineType"])+"__####__"
                    out_roller_machinery_name_operator+=str(roll["operator"])+"__####__"
                    print("out 1",out_machinery_id+" "+out_passes_unit)
                    # print(time_of_application_chemical+"\n"+pitch_main_chemical_weight+"\n"+pitch_main_chemical_unit+"\n"+chemical_details_remark+"\n"+fertilizers_details)
            else:
                    print("No Rollers")
                    
            out_mover_entries_json = (request.POST.get("out_mover_entries_json") or '').strip() or None
            out_mover_entries = json.loads(out_mover_entries_json) if out_mover_entries_json else []
            print("out_mover_entries ",out_mover_entries)
            if(len(out_mover_entries)>0):
                for mov in out_mover_entries:
                    out_mover_machinery_id+=str(mov["machineryId"])+"__####__"
                    out_moving_passes_unit+=str(mov["unit"])+"__####__"
                    out_mowing_duration+=str(mov["duration"])+"__####__"
                    out_date_mowing_done_last+=str(mov["date"])+"__####__"
                    out_time_of_application_mover+=str(mov["time"])+"__####__"
                    out_mover_machine_type+=str(mov["type"])+"__####__"
                    out_mover_machinery_name_operator+=str(mov["operator"])+"__####__"
                    out_mowing_done_at_mm+=str(mov["mowHeight"])+"__####__"
                    print("out 2",out_mover_machinery_id+" "+out_moving_passes_unit)
                    # print(time_of_application_chemical+"\n"+pitch_main_chemical_weight+"\n"+pitch_main_chemical_unit+"\n"+chemical_details_remark+"\n"+fertilizers_details)
            else:
                print("No Movers")
            # Extract outfield entries
            
            out_chemical_entries=(request.POST.get("out_chemical_entries") or '').strip() or None
            out_chemical_entries = json.loads(out_chemical_entries) if out_chemical_entries else []
            print("out_chemical_entries ",out_chemical_entries)
            if(len(out_chemical_entries)>0):
                out_is_fertilizers_used=1
                for chem in out_chemical_entries:
                    out_time_of_application_chemical+=str(chem["time"])+"__####__"
                    outfield_chemical_weight+=str(chem["weight"])+"__####__"
                    outfield_chemical_unit+=str(chem["unit"])+"__####__"
                    out_chemical_details_remark+=str(chem["remark"])+"__####__"
                    out_fertilizers_details+=str(chem["chemical"])+"__####__"
                    # print(time_of_application_chemical+"\n"+pitch_main_chemical_weight+"\n"+pitch_main_chemical_unit+"\n"+chemical_details_remark+"\n"+fertilizers_details)
            else:
                out_is_fertilizers_used=0
                print("No Chemicals")
                print("Outfiled3")
                
            
            practice_machinery_id= ""
            practice_no_of_passes = ""
            practice_rolling_speed = ""
            practice_last_watering_on =  request.POST.get('practice_last_watering_on')
            # print("practice_last_watering_on",practice_last_watering_on)
            practice_quantity_of_water = request.POST.get('practice_quantity_of_water')
            practice_time_of_application = request.POST.get('practice_time_of_application')
            practice_time_roller = ""

            practice_mover_machinery_id = ""
            practice_date_mowing_done_last = ""
            time_of_application_practice_mover = ""
            practice_mowing_done_at_mm = ""
            practice_is_fertilizers_used =  0
            practice_fertilizers_details = ""
            practice_chemical_details_remark= ""
            practice_remark_by_groundsman = ""
            
            
            
            print("practice")
            practice_chemical_entries=(request.POST.get("practice_chemical_entries") or '').strip() or None
            practice_chemical_entries = json.loads(practice_chemical_entries) if practice_chemical_entries else []
            if(len(practice_chemical_entries)>0):
                practice_is_fertilizers_used=1
                for chem in practice_chemical_entries:
                    practice_time_of_application_chemical+=str(chem["time"])+"__####__"
                    practice_area_chemical_weight+=str(chem["weight"])+"__####__"
                    practice_area_chemical_unit+=str(chem["unit"])+"__####__"
                    practice_chemical_details_remark+=str(chem["remark"])+"__####__"
                    practice_fertilizers_details+=str(chem["chemical"])+"__####__"
                    # print(time_of_application_chemical+"\n"+pitch_main_chemical_weight+"\n"+pitch_main_chemical_unit+"\n"+chemical_details_remark+"\n"+fertilizers_details)
            else:
                practice_is_fertilizers_used=0
                print("No Chemicals")

            practice_rolling_entries_json = (request.POST.get("practice_rolling_entries_json") or '').strip() or None
            practice_rolling_entries = json.loads(practice_rolling_entries_json) if practice_rolling_entries_json else []
            if(len(practice_rolling_entries)>0):
                for roll in practice_rolling_entries:
                    practice_machinery_id+=str(roll["machineryId"])+"__####__"
                    practice_passes_unit+=str(roll["unit"])+"__####__"
                    practice_no_of_passes+=str(roll["passes"])+"__####__"
                    practice_rolling_speed+=str(roll["speed"])+"__####__"
                    practice_time_roller+=str(roll["time"])+"__####__"
                    practice_roller_machine_type+=str(roll["machineType"])+"__####__"
                    practice_roller_machinery_name_operator+=str(roll["operator"])+"__####__"
                    print(practice_machinery_id+" "+practice_passes_unit)
                        # print(time_of_application_chemical+"\n"+pitch_main_chemical_weight+"\n"+pitch_main_chemical_unit+"\n"+chemical_details_remark+"\n"+fertilizers_details)
            else:
                print("No Rollers")
                    
            practice_mover_entries_json = (request.POST.get("practice_mover_entries_json") or '').strip() or None
            practice_mover_entries = json.loads(practice_mover_entries_json) if practice_mover_entries_json else []
            if(len(practice_mover_entries)>0):
                practice_is_fertilizers_used=1
                for mov in practice_mover_entries:
                    practice_mover_machinery_id+=str(mov["machineryId"])+"__####__"
                    practice_moving_passes_unit+=str(mov["unit"])+"__####__"
                    practice_mowing_duration+=str(mov["duration"])+"__####__"
                    practice_date_mowing_done_last+=str(mov["date"])+"__####__"
                    time_of_application_practice_mover+=str(mov["time"])+"__####__"
                    practice_mover_machine_type+=str(mov["type"])+"__####__"
                    practice_mover_machinery_name_operator+=str(mov["operator"])+"__####__"
                    practice_mowing_done_at_mm+=str(mov["mowHeight"])+"__####__"
                    print(practice_mover_machinery_id+" "+practice_moving_passes_unit)
                    # print(time_of_application_chemical+"\n"+pitch_main_chemical_weight+"\n"+pitch_main_chemical_unit+"\n"+chemical_details_remark+"\n"+fertilizers_details)
            else:
                practice_is_fertilizers_used=0
                print("No Movers")
            
            btnSubmit = request.POST.get('btnSubmit')
            
            pitch_main =  1 if request.POST.get('pitch-main') else 0
            pitch_practice =  1 if request.POST.get('pitch-practice') else 0
            outfield =  1 if request.POST.get('outfield') else 0
            practice_area =  1 if request.POST.get('practice-area') else 0
            
            
            
            # print(btnSubmit)
            
            # update data into the database
            with connection.cursor() as cursor:
                if(btnSubmit=="Update"):
                    query = f"""UPDATE  {org_id}_curator_daily_recording_master set 
                            pitch_id=%s,
                            recording_type=%s, 
                            ground_id=%s, 
                            pitch_location=%s, 
                            rolling_start_date=%s, 
                            min_temp=%s,
                            max_temp=%s,
                            forecast=%s, 
                            clagg_hammer=%s,
                            moisture=%s, 
                            machinery_id=%s, 
                            no_of_passes=%s, 
                            rolling_speed=%s, 
                            last_watering_on=%s, 
                            quantity_of_water=%s, 
                            time_of_application=%s,
                            time_roller=%s,
                            out_time_roller=%s,
                            mover_machinery_id=%s, 
                            date_mowing_done_last=%s, 
                            time_of_application_mover=%s, 
                            mowing_done_at_mm=%s, 
                            is_fertilizers_used=%s, 
                            fertilizers_details=%s, 
                            chemical_details_remark=%s, 
                            remark_by_groundsman=%s, 
                            out_machinery_id=%s, 
                            out_no_of_passes=%s, 
                            out_rolling_speed=%s, 
                            out_last_watering_on=%s, 
                            out_quantity_of_water=%s, 
                            out_time_of_application=%s, 
                            out_mover_machinery_id=%s, 
                            out_date_mowing_done_last=%s, 
                            time_of_application_out_mover=%s, 
                            out_mowing_done_at_mm=%s, 
                            out_is_fertilizers_used=%s, 
                            out_fertilizers_details=%s, 
                            out_chemical_details_remark=%s, 
                            out_remark_by_groundsman=%s,
                            practice_machinery_id=%s,
                            practice_no_of_passes=%s,
                            practice_rolling_speed=%s,
                            practice_last_watering_on=%s,
                            practice_quantity_of_water=%s,
                            practice_time_of_application=%s,
                            practice_time_roller=%s,
                            practice_mover_machinery_id=%s,
                            practice_date_mowing_done_last=%s,
                            time_of_application_practice_mover=%s,
                            practice_mowing_done_at_mm=%s,
                            practice_is_fertilizers_used=%s,
                            practice_fertilizers_details=%s,
                            practice_chemical_details_remark=%s,
                            practice_remark_by_groundsman=%s,
                             time_of_application_chemical=%s,
                        out_time_of_application_chemical=%s,
                        practice_time_of_application_chemical=%s,
                         pitch_main=%s,pitch_practice=%s,outfield=%s,practice_area=%s,
                          pp_machinery_id=%s, pp_no_of_passes=%s, pp_rolling_speed=%s, pp_last_watering_on=%s,
                        pp_quantity_of_water=%s, pp_time_of_application=%s, pp_time_roller=%s, pp_mover_machinery_id=%s,
                        pp_date_mowing_done_last=%s, pp_time_of_application_mover=%s, pp_mowing_done_at_mm=%s, pp_is_fertilizers_used=%s,
                        pp_fertilizers_details=%s, pp_chemical_details_remark=%s, pp_remark_by_groundsman=%s, pp_time_of_application_chemical=%s,
                        pitch_main_chemical_weight=%s,pitch_practice_chemical_weight=%s,outfield_chemical_weight=%s,practice_area_chemical_weight=%s,
                        pitch_main_chemical_unit=%s,pitch_practice_chemical_unit=%s,outfield_chemical_unit=%s,practice_area_chemical_unit=%s,
                        
                          pp_mover_machine_type=%s, pp_mover_machinery_name_operator=%s , pp_moving_passes_unit=%s ,
                            pp_mowing_duration=%s ,practice_mover_machine_type=%s , practice_mover_machinery_name_operator=%s ,
                            practice_moving_passes_unit=%s ,practice_mowing_duration=%s, out_mover_machine_type=%s ,
                            out_mover_machinery_name_operator=%s, out_moving_passes_unit=%s ,out_mowing_duration=%s ,
                            mover_machine_type=%s , mover_machinery_name_operator=%s ,moving_passes_unit=%s, mowing_duration=%s,
                            roller_machine_type=%s,
                            roller_machinery_name_operator=%s,
                            pp_roller_machine_type=%s,
                            pp_roller_machinery_name_operator=%s,
                            out_roller_machine_type=%s,
                            out_roller_machinery_name_operator=%s,
                            practice_roller_machine_type=%s,
                            practice_roller_machinery_name_operator=%s,
                            passes_unit=%s,
                            out_passes_unit=%s,
                            pp_passes_unit=%s,
                            practice_passes_unit=%s
                        
                            WHERE `id`=%s"""
                    values = [
                    pitch_id_text, 
                    recording_type, 
                    ground_id_text,
                    pitch_location, 
                    rolling_start_date, 
                    min_temp, 
                    max_temp,
                      forecast, 
                      clagg_hammer, 
                      moisture,
                    machinery_id, 
                    no_of_passes, 
                    rolling_speed, 
                    last_watering_on, 
                    quantity_of_water,
                      time_of_application,
                      time_roller,
                      out_time_roller,
                     mover_machinery_id,
                       date_mowing_done_last, 
                       time_of_application_mover,
                    mowing_done_at_mm,
                    is_fertilizers_used, 
                    fertilizers_details, 
                    chemical_details_remark, 
                    remark_by_groundsman,
                    out_machinery_id, 
                    out_no_of_passes,
                      out_rolling_speed,
                        out_last_watering_on,
                          out_quantity_of_water,
                    out_time_of_application, 
                    out_mover_machinery_id, 
                    out_date_mowing_done_last,
                    out_time_of_application_mover, 
                    out_mowing_done_at_mm, 
                    out_is_fertilizers_used,
                    out_fertilizers_details,
                    out_chemical_details_remark, 
                    out_remark_by_groundsman, 
                     practice_machinery_id ,
                        practice_no_of_passes ,
                        practice_rolling_speed ,
                        practice_last_watering_on,
                        practice_quantity_of_water ,
                        practice_time_of_application ,
                        practice_time_roller ,
                        practice_mover_machinery_id ,
                        practice_date_mowing_done_last ,
                        time_of_application_practice_mover ,
                        practice_mowing_done_at_mm ,
                        practice_is_fertilizers_used ,
                        practice_fertilizers_details ,
                        practice_chemical_details_remark,
                        practice_remark_by_groundsman ,
                         time_of_application_chemical,
                    out_time_of_application_chemical,
                    practice_time_of_application_chemical,
                     pitch_main, pitch_practice, outfield, practice_area,
                     pp_machinery_id, pp_no_of_passes, pp_rolling_speed, pp_last_watering_on,
                        pp_quantity_of_water, pp_time_of_application, pp_time_roller, pp_mover_machinery_id,
                        pp_date_mowing_done_last, pp_time_of_application_mover, pp_mowing_done_at_mm, pp_is_fertilizers_used,
                        pp_fertilizers_details, pp_chemical_details_remark, pp_remark_by_groundsman, pp_time_of_application_chemical,
                          pitch_main_chemical_weight, pitch_practice_chemical_weight, outfield_chemical_weight,practice_area_chemical_weight,
                        pitch_main_chemical_unit, pitch_practice_chemical_unit, outfield_chemical_unit, practice_area_chemical_unit,
                         pp_mover_machine_type, pp_mover_machinery_name_operator , pp_moving_passes_unit ,
                            pp_mowing_duration ,practice_mover_machine_type , practice_mover_machinery_name_operator ,
                            practice_moving_passes_unit ,practice_mowing_duration, out_mover_machine_type ,
                            out_mover_machinery_name_operator, out_moving_passes_unit ,out_mowing_duration ,
                            mover_machine_type , mover_machinery_name_operator ,moving_passes_unit, mowing_duration,
                             roller_machine_type,roller_machinery_name_operator,pp_roller_machine_type,
                        pp_roller_machinery_name_operator, out_roller_machine_type,out_roller_machinery_name_operator,
                        practice_roller_machine_type, practice_roller_machinery_name_operator, passes_unit,
                        out_passes_unit,
                        pp_passes_unit,
                        practice_passes_unit ,
                    id
                ]

                elif(btnSubmit=="save"):
                    query = f"""
                        INSERT INTO {org_id}_curator_daily_recording_master (
                            pitch_id,
                            recording_type, 
                            ground_id, 
                            pitch_location, 
                            rolling_start_date, 
                            min_temp, 
                            max_temp, 
                            forecast, 
                            clagg_hammer, 
                            moisture, 
                            machinery_id, 
                            no_of_passes, 
                            rolling_speed, 
                            last_watering_on, 
                            quantity_of_water, 
                            time_of_application,
                            time_roller,
                            out_time_roller,
                            mover_machinery_id, 
                            date_mowing_done_last,
                            time_of_application_mover, 
                            mowing_done_at_mm, 
                            is_fertilizers_used, 
                            fertilizers_details, 
                            chemical_details_remark, 
                            remark_by_groundsman, 
                            out_machinery_id, 
                            out_no_of_passes, 
                            out_rolling_speed, 
                            out_last_watering_on, 
                            out_quantity_of_water, 
                            out_time_of_application,
                            out_mover_machinery_id, 
                            out_date_mowing_done_last, 
                            time_of_application_out_mover, 
                            out_mowing_done_at_mm, 
                            out_is_fertilizers_used, 
                            out_fertilizers_details, 
                            out_chemical_details_remark, 
                            out_remark_by_groundsman,
                             practice_machinery_id ,
                        practice_no_of_passes ,
                        practice_rolling_speed ,
                        practice_last_watering_on,
                        practice_quantity_of_water ,
                        practice_time_of_application ,
                        practice_time_roller ,

                        practice_mover_machinery_id ,
                        practice_date_mowing_done_last ,
                        time_of_application_practice_mover ,
                        practice_mowing_done_at_mm ,
                        practice_is_fertilizers_used ,
                        practice_fertilizers_details ,
                        practice_chemical_details_remark,
                        practice_remark_by_groundsman,
                         time_of_application_chemical,
                        out_time_of_application_chemical,
                        practice_time_of_application_chemical,
                        pp_machinery_id, pp_no_of_passes, pp_rolling_speed, pp_last_watering_on,
                        pp_quantity_of_water, pp_time_of_application, pp_time_roller, pp_mover_machinery_id,
                        pp_date_mowing_done_last, pp_time_of_application_mover, pp_mowing_done_at_mm, pp_is_fertilizers_used,
                        pp_fertilizers_details, pp_chemical_details_remark, pp_remark_by_groundsman, pp_time_of_application_chemical,
                       
                         pitch_main_chemical_weight,pitch_practice_chemical_weight,outfield_chemical_weight,practice_area_chemical_weight,
                            pitch_main_chemical_unit,pitch_practice_chemical_unit,outfield_chemical_unit,practice_area_chemical_unit,
                              pp_mover_machine_type, pp_mover_machinery_name_operator , pp_moving_passes_unit ,
                            pp_mowing_duration ,practice_mover_machine_type , practice_mover_machinery_name_operator ,
                            practice_moving_passes_unit ,practice_mowing_duration, out_mover_machine_type ,
                            out_mover_machinery_name_operator, out_moving_passes_unit ,out_mowing_duration ,
                            mover_machine_type , mover_machinery_name_operator ,moving_passes_unit, mowing_duration,
                            roller_machine_type,
                            roller_machinery_name_operator,
                            pp_roller_machine_type,
                            pp_roller_machinery_name_operator,
                            out_roller_machine_type,
                            out_roller_machinery_name_operator,
                            practice_roller_machine_type,
                            practice_roller_machinery_name_operator,
                            passes_unit,
                            out_passes_unit,
                            pp_passes_unit,
                            practice_passes_unit
                        
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
                                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
                                %s, %s, %s, %s, %s, %s,%s,%s, %s, %s, %s, %s, %s, %s, %s,
                      %s, %s, %s, %s, %s, %s, %s,%s, %s, %s,%s,%s, %s, %s,%s,%s, %s, %s,%s,%s, %s, %s,%s,%s, %s, %s,%s,%s,%s,%s,%s,%s,%s,%s
                      ,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                        """
                    values = [
                    pitch_id_text, 
                    recording_type, 
                    ground_id_text,
                    pitch_location, 
                    rolling_start_date, 
                    min_temp, 
                    max_temp,
                      forecast, 
                      clagg_hammer, 
                      moisture,
                    machinery_id, 
                    no_of_passes, 
                    rolling_speed, 
                    last_watering_on, 
                    quantity_of_water,
                      time_of_application,
                      time_roller,
                      out_time_roller,
                     mover_machinery_id,
                       date_mowing_done_last, 
                       time_of_application_mover,
                    mowing_done_at_mm,
                    is_fertilizers_used, 
                    fertilizers_details, 
                    chemical_details_remark, 
                    remark_by_groundsman,
                    out_machinery_id, 
                    out_no_of_passes,
                      out_rolling_speed,
                        out_last_watering_on,
                          out_quantity_of_water,
                    out_time_of_application, 
                    out_mover_machinery_id, 
                    out_date_mowing_done_last,
                    out_time_of_application_mover, 
                    out_mowing_done_at_mm, 
                    out_is_fertilizers_used,
                    out_fertilizers_details,
                    out_chemical_details_remark, 
                    out_remark_by_groundsman, 
                     practice_machinery_id ,
                        practice_no_of_passes ,
                        practice_rolling_speed ,
                        practice_last_watering_on,
                        practice_quantity_of_water ,
                        practice_time_of_application ,
                        practice_time_roller ,
                     

                        practice_mover_machinery_id ,
                        practice_date_mowing_done_last ,
                        time_of_application_practice_mover ,
                        practice_mowing_done_at_mm ,
                        practice_is_fertilizers_used ,
                        practice_fertilizers_details ,
                        practice_chemical_details_remark,
                        practice_remark_by_groundsman ,
                        time_of_application_chemical,
                    out_time_of_application_chemical,
                    practice_time_of_application_chemical,
                    pp_machinery_id, pp_no_of_passes, pp_rolling_speed, pp_last_watering_on,
                        pp_quantity_of_water, pp_time_of_application, pp_time_roller, pp_mover_machinery_id,
                        pp_date_mowing_done_last, pp_time_of_application_mover, pp_mowing_done_at_mm, pp_is_fertilizers_used,
                        pp_fertilizers_details, pp_chemical_details_remark, pp_remark_by_groundsman, pp_time_of_application_chemical,
                         pitch_main_chemical_weight,pitch_practice_chemical_weight,outfield_chemical_weight,practice_area_chemical_weight,
                            pitch_main_chemical_unit,pitch_practice_chemical_unit,outfield_chemical_unit,practice_area_chemical_unit,
                            pp_mover_machine_type, pp_mover_machinery_name_operator , pp_moving_passes_unit ,
                            pp_mowing_duration ,practice_mover_machine_type , practice_mover_machinery_name_operator ,
                            practice_moving_passes_unit ,practice_mowing_duration, out_mover_machine_type ,
                            out_mover_machinery_name_operator, out_moving_passes_unit ,out_mowing_duration ,
                            mover_machine_type , mover_machinery_name_operator ,moving_passes_unit, mowing_duration,
                             roller_machine_type,roller_machinery_name_operator,pp_roller_machine_type,
                        pp_roller_machinery_name_operator, out_roller_machine_type,out_roller_machinery_name_operator,
                        practice_roller_machine_type, practice_roller_machinery_name_operator, passes_unit,
                        out_passes_unit,
                        pp_passes_unit,
                        practice_passes_unit
                        
                    
                ]



                # Debugging: Print the query and values
                print("Query:", query)
                print("Values:", values)

                cleaned_values = [
    value if value not in ['NA', 'None', '', None] else None
    for value in values
]


                cursor.execute(query, cleaned_values)
                # print("Hello")
         
         
         
         
            return redirect('curator_daily_recording_list')


        

        return render(request, 'admin_user/update_daily_recording_form.html', {'daily': dailyRecord})
    except Exception as e:
        print(e)

@csrf_exempt
def delete_daily(request,daily_id):
    org_id = request.session["org_id"]
    if request.method == 'DELETE':
        with connection.cursor() as cursor:
            # Delete score by id
            cursor.execute(f"""DELETE FROM {org_id}_curator_daily_recording_master WHERE id = %s""", [daily_id])

        return JsonResponse({'status': 'success'})

    
def curator_daily_recording_list_filter(request):
    org_id = request.session["org_id"]
    ground_id = request.GET.get("ground_id")
    with connection.cursor() as cursor:
        try:
            sql = f'''
                    SELECT 
                        cdr.id, 
                        cdr.pitch_id, 
                        cdr.pitch_location, 
                        cdr.rolling_start_date, 
                        cdr.min_temp, 
                        cdr.max_temp, 
                        cdr.forecast, 
                        cdr.clagg_hammer, 
                        cdr.moisture, 
                        cdr.machinery_id, 
                        cdr.no_of_passes, 
                        cdr.rolling_speed, 
                        cdr.last_watering_on, 
                        cdr.quantity_of_water, 
                        cdr.time_of_application, 
                        cdr.time_roller, 
                        cdr.mover_machinery_id, 
                        cdr.date_mowing_done_last, 
                        cdr.time_of_application_mover, 
                        cdr.mowing_done_at_mm, 
                        cdr.is_fertilizers_used, 
                        cdr.fertilizers_details, 
                        cdr.chemical_details_remark, 
                        cdr.remark_by_groundsman, 
                        cdr.out_machinery_id, 
                        cdr.out_no_of_passes, 
                        cdr.out_rolling_speed, 
                        cdr.out_last_watering_on, 
                        cdr.out_quantity_of_water, 
                        cdr.out_time_of_application, 
                        cdr.out_time_roller, 
                        cdr.out_mover_machinery_id, 
                        cdr.out_date_mowing_done_last, 
                        cdr.time_of_application_out_mover, 
                        cdr.out_mowing_done_at_mm, 
                        cdr.out_is_fertilizers_used, 
                        cdr.out_fertilizers_details, 
                        cdr.out_chemical_details_remark, 
                        cdr.out_remark_by_groundsman, 
                        cdr.practice_machinery_id, 
                        cdr.practice_no_of_passes, 
                        cdr.practice_rolling_speed, 
                        cdr.practice_last_watering_on, 
                        cdr.practice_quantity_of_water, 
                        cdr.practice_time_of_application, 
                        cdr.practice_time_roller, 
                        cdr.practice_mover_machinery_id, 
                        cdr.practice_date_mowing_done_last, 
                        cdr.time_of_application_practice_mover, 
                        cdr.practice_mowing_done_at_mm, 
                        cdr.practice_is_fertilizers_used, 
                        cdr.practice_fertilizers_details, 
                        cdr.practice_chemical_details_remark, 
                        cdr.practice_remark_by_groundsman, 
                        cdr.time_of_application_chemical, 
                        cdr.out_time_of_application_chemical, 
                        cdr.practice_time_of_application_chemical, 
                        cdr.recording_type, 
                        cdr.ground_id, 
                        cdr.created_at, 
                        cdr.updated_at,
                        p.pitch_type, 
                        p.pitch_placement, 
                        g.ground_name AS ground_name,
                        m1.print_details AS main_machinery,
                        m2.print_details AS mover_machinery,
                        m3.print_details AS out_machinery,
                        m4.print_details AS out_mover_machinery,
                        m5.print_details AS practice_machinery,
                        m6.print_details AS practice_mover_machinery,
                        cdr.pitch_main,
                        cdr.pitch_practice,
                        cdr.outfield,
                        cdr.practice_area,
                        cdr.pp_machinery_id, 
                        cdr.pp_no_of_passes, 
                        cdr.pp_rolling_speed, 
                        cdr.pp_last_watering_on,
                        cdr.pp_quantity_of_water, 
                        cdr.pp_time_of_application, 
                        cdr.pp_time_roller, 
                        cdr.pp_mover_machinery_id,
                        cdr.pp_date_mowing_done_last, 
                        cdr.pp_time_of_application_mover, 
                        cdr.pp_mowing_done_at_mm, 
                        cdr.pp_is_fertilizers_used,
                        cdr.pp_fertilizers_details, 
                        cdr.pp_chemical_details_remark, 
                        cdr.pp_remark_by_groundsman,
                        cdr.pp_time_of_application_chemical,
                        m7.print_details AS pp_machinery,
                        m8.print_details AS pp_mover_machinery,
                        cdr.pitch_main_chemical_unit,
                        cdr.pitch_main_chemical_weight,
                        cdr.pitch_practice_chemical_weight,
                        cdr.pitch_practice_chemical_unit,
                        cdr.outfield_chemical_weight,
                        cdr.outfield_chemical_unit,
                        cdr.practice_area_chemical_weight,
                        cdr.practice_area_chemical_unit
                    FROM 
                        {org_id}_curator_daily_recording_master cdr
                    INNER JOIN 
                        {org_id}_pitch_master p ON cdr.pitch_id = p.id
                    INNER JOIN 
                        {org_id}_ground_master g ON cdr.ground_id = g.id
                    LEFT JOIN 
                        {org_id}_machinery_master m1 ON cdr.machinery_id = m1.id
                    LEFT JOIN 
                        {org_id}_machinery_master m2 ON cdr.mover_machinery_id = m2.id
                    LEFT JOIN 
                        {org_id}_machinery_master m3 ON cdr.out_machinery_id = m3.id
                    LEFT JOIN 
                        {org_id}_machinery_master m4 ON cdr.out_mover_machinery_id = m4.id
                    LEFT JOIN 
                        {org_id}_machinery_master m5 ON cdr.practice_machinery_id = m5.id
                    LEFT JOIN 
                        {org_id}_machinery_master m6 ON cdr.practice_mover_machinery_id = m6.id
                        LEFT JOIN 
                        {org_id}_machinery_master m7 ON cdr.pp_machinery_id = m7.id
                        LEFT JOIN 
                        {org_id}_machinery_master m8 ON cdr.pp_mover_machinery_id = m8.id
                        WHERE cdr.ground_id = %s order by cdr.created_at desc;
                '''
               
            cursor.execute(sql, [ground_id])
            recordings = cursor.fetchall()
            
        except Exception as e:
            print(e)
            messages.error(request, e)
        return render(request, 'admin_user/curator_daily_recording_list.html', {'recordings': recordings, "flag": True})

    
def curator_daily_recording_list(request):
    org_id = request.session["org_id"]
    with connection.cursor() as cursor:
        user = request.session.get("user")
        try:
            if user.get("role") == "admin":
                sql = f'''
                    SELECT 
                        cdr.id, 
                        cdr.pitch_id, 
                        cdr.pitch_location, 
                        cdr.rolling_start_date, 
                        cdr.min_temp, 
                        cdr.max_temp, 
                        cdr.forecast, 
                        cdr.clagg_hammer, 
                        cdr.moisture, 
                        cdr.machinery_id, 
                        cdr.no_of_passes, 
                        cdr.rolling_speed, 
                        cdr.last_watering_on, 
                        cdr.quantity_of_water, 
                        cdr.time_of_application, 
                        cdr.time_roller, 
                        cdr.mover_machinery_id, 
                        cdr.date_mowing_done_last, 
                        cdr.time_of_application_mover, 
                        cdr.mowing_done_at_mm, 
                        cdr.is_fertilizers_used, 
                        cdr.fertilizers_details, 
                        cdr.chemical_details_remark, 
                        cdr.remark_by_groundsman, 
                        cdr.out_machinery_id, 
                        cdr.out_no_of_passes, 
                        cdr.out_rolling_speed, 
                        cdr.out_last_watering_on, 
                        cdr.out_quantity_of_water, 
                        cdr.out_time_of_application, 
                        cdr.out_time_roller, 
                        cdr.out_mover_machinery_id, 
                        cdr.out_date_mowing_done_last, 
                        cdr.time_of_application_out_mover, 
                        cdr.out_mowing_done_at_mm, 
                        cdr.out_is_fertilizers_used, 
                        cdr.out_fertilizers_details, 
                        cdr.out_chemical_details_remark, 
                        cdr.out_remark_by_groundsman, 
                        cdr.practice_machinery_id, 
                        cdr.practice_no_of_passes, 
                        cdr.practice_rolling_speed, 
                        cdr.practice_last_watering_on, 
                        cdr.practice_quantity_of_water, 
                        cdr.practice_time_of_application, 
                        cdr.practice_time_roller, 
                        cdr.practice_mover_machinery_id, 
                        cdr.practice_date_mowing_done_last, 
                        cdr.time_of_application_practice_mover, 
                        cdr.practice_mowing_done_at_mm, 
                        cdr.practice_is_fertilizers_used, 
                        cdr.practice_fertilizers_details, 
                        cdr.practice_chemical_details_remark, 
                        cdr.practice_remark_by_groundsman, 
                        cdr.time_of_application_chemical, 
                        cdr.out_time_of_application_chemical, 
                        cdr.practice_time_of_application_chemical, 
                        cdr.recording_type, 
                        cdr.ground_id, 
                        cdr.created_at, 
                        cdr.updated_at,
                        p.pitch_type, 
                        p.pitch_placement, 
                        g.ground_name AS ground_name,
                        m1.print_details AS main_machinery,
                        m2.print_details AS mover_machinery,
                        m3.print_details AS out_machinery,
                        m4.print_details AS out_mover_machinery,
                        m5.print_details AS practice_machinery,
                        m6.print_details AS practice_mover_machinery,
                        cdr.pitch_main,
                        cdr.pitch_practice,
                        cdr.outfield,
                        cdr.practice_area,
                        cdr.pp_machinery_id, 
                        cdr.pp_no_of_passes, 
                        cdr.pp_rolling_speed, 
                        cdr.pp_last_watering_on,
                        cdr.pp_quantity_of_water, 
                        cdr.pp_time_of_application, 
                        cdr.pp_time_roller, 
                        cdr.pp_mover_machinery_id,
                        cdr.pp_date_mowing_done_last, 
                        cdr.pp_time_of_application_mover, 
                        cdr.pp_mowing_done_at_mm, 
                        cdr.pp_is_fertilizers_used,
                        cdr.pp_fertilizers_details, 
                        cdr.pp_chemical_details_remark, 
                        cdr.pp_remark_by_groundsman,
                        cdr.pp_time_of_application_chemical,
                        m7.print_details AS pp_machinery,
                        m8.print_details AS pp_mover_machinery,
                        cdr.pitch_main_chemical_unit,
                        cdr.pitch_main_chemical_weight,
                        cdr.pitch_practice_chemical_weight,
                        cdr.pitch_practice_chemical_unit,
                        cdr.outfield_chemical_weight,
                        cdr.outfield_chemical_unit,
                        cdr.practice_area_chemical_weight,
                        cdr.practice_area_chemical_unit
                    FROM 
                        {org_id}_curator_daily_recording_master cdr
                    INNER JOIN 
                        {org_id}_pitch_master p ON cdr.pitch_id = p.id
                    INNER JOIN 
                        {org_id}_ground_master g ON cdr.ground_id = g.id
                    LEFT JOIN 
                        {org_id}_machinery_master m1 ON cdr.machinery_id = m1.id
                    LEFT JOIN 
                        {org_id}_machinery_master m2 ON cdr.mover_machinery_id = m2.id
                    LEFT JOIN 
                        {org_id}_machinery_master m3 ON cdr.out_machinery_id = m3.id
                    LEFT JOIN 
                        {org_id}_machinery_master m4 ON cdr.out_mover_machinery_id = m4.id
                    LEFT JOIN 
                        {org_id}_machinery_master m5 ON cdr.practice_machinery_id = m5.id
                    LEFT JOIN 
                        {org_id}_machinery_master m6 ON cdr.practice_mover_machinery_id = m6.id
                        LEFT JOIN 
                        {org_id}_machinery_master m7 ON cdr.pp_machinery_id = m7.id
                        LEFT JOIN 
                        {org_id}_machinery_master m8 ON cdr.pp_mover_machinery_id = m8.id
                    order by cdr.created_at desc;
                '''
                cursor.execute(sql)
            else:
                sql = f'''
                    SELECT 
                        cdr.id, 
                        cdr.pitch_id, 
                        cdr.pitch_location, 
                        cdr.rolling_start_date, 
                        cdr.min_temp, 
                        cdr.max_temp, 
                        cdr.forecast, 
                        cdr.clagg_hammer, 
                        cdr.moisture, 
                        cdr.machinery_id, 
                        cdr.no_of_passes, 
                        cdr.rolling_speed, 
                        cdr.last_watering_on, 
                        cdr.quantity_of_water, 
                        cdr.time_of_application, 
                        cdr.time_roller, 
                        cdr.mover_machinery_id, 
                        cdr.date_mowing_done_last, 
                        cdr.time_of_application_mover, 
                        cdr.mowing_done_at_mm, 
                        cdr.is_fertilizers_used, 
                        cdr.fertilizers_details, 
                        cdr.chemical_details_remark, 
                        cdr.remark_by_groundsman, 
                        cdr.out_machinery_id, 
                        cdr.out_no_of_passes, 
                        cdr.out_rolling_speed, 
                        cdr.out_last_watering_on, 
                        cdr.out_quantity_of_water, 
                        cdr.out_time_of_application, 
                        cdr.out_time_roller, 
                        cdr.out_mover_machinery_id, 
                        cdr.out_date_mowing_done_last, 
                        cdr.time_of_application_out_mover, 
                        cdr.out_mowing_done_at_mm, 
                        cdr.out_is_fertilizers_used, 
                        cdr.out_fertilizers_details, 
                        cdr.out_chemical_details_remark, 
                        cdr.out_remark_by_groundsman, 
                        cdr.practice_machinery_id, 
                        cdr.practice_no_of_passes, 
                        cdr.practice_rolling_speed, 
                        cdr.practice_last_watering_on, 
                        cdr.practice_quantity_of_water, 
                        cdr.practice_time_of_application, 
                        cdr.practice_time_roller, 
                        cdr.practice_mover_machinery_id, 
                        cdr.practice_date_mowing_done_last, 
                        cdr.time_of_application_practice_mover, 
                        cdr.practice_mowing_done_at_mm, 
                        cdr.practice_is_fertilizers_used, 
                        cdr.practice_fertilizers_details, 
                        cdr.practice_chemical_details_remark, 
                        cdr.practice_remark_by_groundsman, 
                        cdr.time_of_application_chemical, 
                        cdr.out_time_of_application_chemical, 
                        cdr.practice_time_of_application_chemical, 
                        cdr.recording_type, 
                        cdr.ground_id, 
                        cdr.created_at, 
                        cdr.updated_at, 
                        p.pitch_type, 
                        p.pitch_placement, 
                        g.ground_name AS ground_name,
                        m1.print_details AS main_machinery,
                        m2.print_details AS mover_machinery,
                        m3.print_details AS out_machinery,
                        m4.print_details AS out_mover_machinery,
                        m5.print_details AS practice_machinery,
                        m6.print_details AS practice_mover_machinery,
                        cdr.pitch_main,
                        cdr.pitch_practice,
                        cdr.outfield,
                        cdr.practice_area,
                        cdr.pp_machinery_id, cdr.pp_no_of_passes, cdr.pp_rolling_speed, cdr.pp_last_watering_on,
                        cdr.pp_quantity_of_water, cdr.pp_time_of_application, cdr.pp_time_roller, cdr.pp_mover_machinery_id,
                        cdr.pp_date_mowing_done_last, cdr.pp_time_of_application_mover, cdr.pp_mowing_done_at_mm, cdr.pp_is_fertilizers_used,
                        cdr.pp_fertilizers_details, cdr.pp_chemical_details_remark, cdr.pp_remark_by_groundsman, cdr.pp_time_of_application_chemical,
                        m7.print_details AS pp_machinery,
                        m8.print_details AS pp_mover_machinery,
                        cdr.pitch_main_chemical_unit,
                        cdr.pitch_main_chemical_weight
                    FROM 
                        {org_id}_curator_daily_recording_master cdr
                    INNER JOIN 
                        {org_id}_pitch_master p ON cdr.pitch_id = p.id
                    INNER JOIN 
                        {org_id}_ground_master g ON cdr.ground_id = g.id
                    LEFT JOIN 
                        {org_id}_machinery_master m1 ON cdr.machinery_id = m1.id
                    LEFT JOIN 
                        {org_id}_machinery_master m2 ON cdr.mover_machinery_id = m2.id
                    LEFT JOIN 
                        {org_id}_machinery_master m3 ON cdr.out_machinery_id = m3.id
                    LEFT JOIN 
                        {org_id}_machinery_master m4 ON cdr.out_mover_machinery_id = m4.id
                    LEFT JOIN 
                        {org_id}_machinery_master m5 ON cdr.practice_machinery_id = m5.id
                    LEFT JOIN 
                        {org_id}_machinery_master m6 ON cdr.practice_mover_machinery_id = m6.id
                        LEFT JOIN 
                        {org_id}_machinery_master m7 ON cdr.pp_machinery_id = m7.id
                        LEFT JOIN 
                        {org_id}_machinery_master m8 ON cdr.pp_mover_machinery_id = m8.id
                    
                    WHERE cdr.ground_id = %s order by cdr.created_at desc;
                '''
                cursor.execute(sql, [user.get("ground_id")])
            recordings = cursor.fetchall()
            
        except Exception as e:
            print(e)
            messages.error(request, e)
        return render(request, 'admin_user/curator_daily_recording_list.html', {'recordings': recordings, "flag": True})


# Fetch All Machinery
def machinery_list(request):
    org_id = request.session["org_id"]
    with connection.cursor() as cursor:
        cursor.execute(f'SELECT * FROM {org_id}_machinery_master')
        machinery = cursor.fetchall()
    return render(request, 'admin_user/machinery_list.html', {'machinery': machinery})


# Insert Machinery
def insert_machinery(request):
    try:
        org_id = request.session["org_id"]
        if request.method == 'POST':
            equipment_name = request.POST.get('equipment_name')
            equipment_model = request.POST.get('equipment_model')
            type_ = request.POST.get('type')
            # company = request.POST.get('company')
            date_purchase = request.POST.get('date_purchase')
            unit = request.POST.get('unit')
            value = request.POST.get('value')
            details = request.POST.get('print_details')

            with connection.cursor() as cursor:
                cursor.execute(f'''INSERT INTO {org_id}_machinery_master
    (`equipment_name`,`type`,`date_purchase`,`unit`,`value`,`model`,`print_details`) VALUES (%s,%s,%s,%s,%s,%s,%s)''',
    [equipment_name, type_,date_purchase,unit,value,equipment_model,details ])

            return redirect('machinery_list')

        return render(request, 'admin_user/machinery_master.html')
    except Exception as e:
        print(e)


@csrf_exempt
def delete_machinery(request,machinery_id):
    org_id = request.session["org_id"]
    if request.method == 'DELETE':
        with connection.cursor() as cursor:
            # Delete score by id
            cursor.execute(f"""DELETE FROM {org_id}_machinery_master WHERE id = %s""", [machinery_id])

        return JsonResponse({'status': 'success'})


def get_machinery_data(request):
    org_id = request.session["org_id"]
    with connection.cursor() as cursor:
        try:
            sql=f"SELECT * FROM {org_id}_machinery_master"
            print(sql)
            cursor.execute(f"SELECT * FROM {org_id}_machinery_master")

            data = cursor.fetchall()
            columns = [col[0] for col in cursor.description]
            machinery_data = [dict(zip(columns, row)) for row in data]
            return JsonResponse(machinery_data, safe=False)
        except Exception as e:
            print(e)

    return JsonResponse(machinery_data, safe=False)


# Update Machinery
def update_machinery(request, machinery_id):

    try:
        org_id = request.session["org_id"]
        with connection.cursor() as cursor:
            cursor.execute(f'SELECT * FROM {org_id}_machinery_master WHERE id = %s', [machinery_id])
            machinery = cursor.fetchone()


        if request.method == 'POST':
            equipment_name = request.POST.get('equipment_name')
            equipment_model = request.POST.get('equipment_model')
            type_ = request.POST.get('type')
            # company = request.POST.get('company')
            specification = request.POST.get('specification')
            unit = request.POST.get('unit')
            value = request.POST.get('value')
            details = request.POST.get('print_details')

            with connection.cursor() as cursor:
                cursor.execute(f'''
                UPDATE {org_id}_machinery_master
SET `equipment_name` = %s,`type` = %s,`specification` = %s,`unit` = %s,`value` = %s,
`model` = %s ,`print_details` = %s WHERE `id` = %s'''
    , [equipment_name, type_,specification,unit,value,equipment_model ,details,machinery_id])

            return redirect('machinery_list')
        print(machinery)
        return render(request, 'admin_user/update_machinery.html', {'machinery': machinery})
    except Exception as e:
        print(e)


def get_machinery_details(request, machinery_id):
    org_id = request.session["org_id"]
    with connection.cursor() as cursor:
        cursor.execute(f"SELECT *  FROM {org_id}_machinery_master WHERE id = %s", [machinery_id])
        row = cursor.fetchone()

    if row:
        data = {
            'id': row[0],
            'equipment_name': row[1],
            'model': row[2],
            'type': row[3],

            'specification': row[4],
            'unit': row[5],
            'value': row[6],
            'print_details': row[7],
        }
        return JsonResponse({'machinery': data})
    else:
        return JsonResponse({'error': 'Machinery not found'}, status=404)

def add_score(request, match_id):
    try:
        org_id = request.session["org_id"]
        query = f"SELECT * FROM {org_id}_match_master WHERE id = %s;"
        with connection.cursor() as cursor:
            cursor.execute(query, [match_id])
            match = cursor.fetchone()

        if request.method == "POST":
            team1_score = request.POST.get('team1_score')
            team2_score = request.POST.get('team2_score')
            team1_wickets = request.POST.get('team1_wickets')
            team2_wickets = request.POST.get('team2_wickets')
            overs = request.POST.get('overs')
            winner = request.POST.get('winner')
            dayEnd = request.POST.get('day-end')

            if match[1] == 'Test':  # If it's a Test match, store scores by day
                day = request.POST.get('day')
                query = f"""
                    INSERT INTO {org_id}_match_scores_master (match_id, day, team1_score, team2_score, team1_wickets, team2_wickets, overs, winner,day_end)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s,%s);
                """
                with connection.cursor() as cursor:
                    cursor.execute(query, [match_id, day, team1_score, team2_score, team1_wickets, team2_wickets, overs, winner,dayEnd])
            else:
                query = f"""
                    INSERT INTO {org_id}_match_scores_master (match_id, team1_score, team2_score, team1_wickets, team2_wickets, overs, winner,day_end)
                    VALUES (%s, %s, %s, %s, %s, %s, %s,%s);
                """
                with connection.cursor() as cursor:
                    cursor.execute(query, [match_id, team1_score, team2_score, team1_wickets, team2_wickets, overs, winner,dayEnd])

            return redirect('list_matches')

     
        print(match)

        return render(request, 'admin_user/score_form.html', {'match': match})
    except Exception as e:
        print(e)

@csrf_exempt
def save_scores(request):
    try:
        org_id = request.session["org_id"]
        if request.method == 'POST':
            data = json.loads(request.body)
            match_id = data.get('match_id')
            scores = data.get('scores')
            i=1
            print(scores)
            with connection.cursor() as cursor:
                
                for score in scores:
                    day = score.get('day')
                    inning = score.get('inning')
                    team = score.get('team')
                    session = score.get('session')
                    runs = score.get('runs')
                    wickets = score.get('wickets')
                    overs = score.get('overs')
                    winner = score.get('winner')
                    dayEnd = score.get('dayEnd')
                    remark = score.get('remark')
                    tossWon = score.get('wonby')
                    elected = score.get('elected')
                    
                    if(i==1 and score["save"]==True):

                        # Insert the score into the match_scores table
                        cursor.execute(f"""
                            INSERT INTO {org_id}_match_scores_master (match_id, day, inning, team, session, 
                            runs, wickets, overs, winner,day_end,remark,wonby,elected)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """, [match_id, day, inning, team, session, runs, wickets, overs, winner, dayEnd, remark, tossWon, elected])
                    else:
                        cursor.execute(f"""
                            INSERT INTO {org_id}_match_scores_master (match_id, day, inning, team, session, 
                            runs, wickets, overs, winner,day_end,remark)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """, [match_id, day, inning, team, session, runs, wickets, overs, winner, dayEnd, remark])
                    i+=1

            return JsonResponse({'status': 'success'})
    except Exception as e:
        print(e)

@csrf_exempt
def get_match_scores(request, match_id):
    try:
        org_id = request.session["org_id"]
        if request.method == 'GET':
            with connection.cursor() as cursor:
                # Fetch scores based on match_id
                cursor.execute(f"""
                    SELECT `{org_id}_match_scores_master`.id, day, inning, team, session, runs, wickets, overs, winner,day_end, 
                    `{org_id}_match_master`.match_type,`{org_id}_match_master`.team1,`{org_id}_match_master`.team2,remark, wonby, elected
                    FROM {org_id}_match_scores_master inner join {org_id}_match_master on `{org_id}_match_scores_master`.match_id=`{org_id}_match_master`.id
                    WHERE match_id = %s
                """, [match_id])
                scores = cursor.fetchall()
                
                cursor.execute(f"""SELECT match_type, name_tournament, match_date, from_date, to_date ,ground_id FROM `{org_id}_match_master` WHERE id = %s""", [match_id])
                match = cursor.fetchone()
                print(match)
                
                cursor.execute(f"""SELECT ground_name FROM `{org_id}_ground_master` WHERE id = %s""", [match[5]])
                ground = cursor.fetchone()
                print(ground)
                
            # Format the response data
            scores_data = [
                {
                    'id': row[0],
                    'day': row[1],
                    'inning': row[2],
                    'team': row[3],
                    'session': row[4],
                    'runs': row[5],
                    'wickets': row[6],
                    'overs': row[7],
                    'winner': row[8],
                    'day_end': row[9],
                    'match_type': row[10],
                    'team1': row[11],
                    'team2': row[12],
                    'remark': row[13],
                    'wonby': row[14],
                    'elected': row[15],
                }
                for row in scores
            ]

            return JsonResponse({'scores': scores_data, 'match': match,'ground':ground})
    except Exception as e:
        print(e)

def match_scores_list(request,match_id):
    return render(request, "admin_user/match_scores_list.html", {"match_id": match_id})


@csrf_exempt
def delete_score(request, score_id):
    org_id = request.session["org_id"]
    if request.method == 'DELETE':
        with connection.cursor() as cursor:
            # Delete score by id
            cursor.execute(f"""
                DELETE FROM {org_id}_match_scores_master
                WHERE id = %s
            """, [score_id])

        return JsonResponse({'status': 'success'})



@csrf_exempt
def update_score(request, score_id):
    org_id = request.session["org_id"]
    try:
        if request.method == 'PUT':
            data = json.loads(request.body)
            day = data.get('day')
            inning = data.get('inning')
            team = data.get('team')
            session = data.get('session')
            runs = data.get('runs')
            wickets = data.get('wickets')
            overs = data.get('overs')
            winner = data.get('winner')
            dayEnd = data.get('dayEnd')
            remark = data.get('remark')

            with connection.cursor() as cursor:
                # Update the score entry
                cursor.execute(f"""
                    UPDATE {org_id}_match_scores_master
                    SET day = %s, inning = %s, team = %s, session = %s, runs = %s, wickets = %s, overs = %s, winner = %s,day_end=%s,remark=%s
                    WHERE id = %s
                """, [day, inning, team, session, runs, wickets, overs, winner, dayEnd,remark,score_id])

            return JsonResponse({'status': 'success'})
    except Exception as e:
        print(e)

 
def insert_match(request):
    try:
        org_id = request.session["org_id"]
        if request.method == 'POST':
            rowIndxs=request.POST.get("rowIndxs")
            print("rowIndxs",rowIndxs)
            rowSplit=rowIndxs.split("-")
            pitchIndex=int(rowSplit[0].strip())
            outfieldIndex=int(rowSplit[1].strip())
          
          
            # print(pitchIndex,outfieldIndex)
            maxIndex=max(pitchIndex,outfieldIndex)
            print("Max Index=",maxIndex)
            
            
            for index in range(1,maxIndex+1):
            
                match_type = request.POST.get('match_type')
                name_tournament = request.POST.get('name_tournament')
                team1 = request.POST.get('team1')
                team2 = request.POST.get('team2')
                preparation_date = request.POST.get('preparation_date')
                match_date = request.POST.get('match_date')
                from_date = request.POST.get('from_date')
                to_date = request.POST.get('to_date')
                days_count = request.POST.get('days_count')
                start_time = request.POST.get('start_time')
                pitch_id = request.POST.get('pitch_id')
                ground_id = request.POST.get('ground_id')
                is_pitch_level = request.POST.get('is_pitch_level', 'off') == 'on'
                lawn_height = request.POST.get('lawn_height')
                grass_cover = request.POST.get('grass_cover')
                min_temp = request.POST.get('min_temp')
                max_temp = request.POST.get('max_temp')
                forecast = request.POST.get('forecast')
                moisture_upto = request.POST.get('moisture_upto')
                dew_factor =request.POST.get('dew_factor')
                access_bounce =request.POST.get('access_bounce')
                nuteral_curator =request.POST.get('nuteral_curator')
                # rolling_time = request.POST.get('rolling_time')
                # rolling_pattern = request.POST.get('rolling_pattern')
                if(pitchIndex>0):
                    machinery_id = ""
                    passes_unit = ""
                    rolling_date=""
                    no_of_passes = ""
                    rolling_speed =""
                    last_watering_on = ""
                    quantity_of_water =""
                    time_of_application = ""
                    # last_watering_on = (request.POST.get('last_watering_on'+str(index)) or '').strip() or None
                    # quantity_of_water = (request.POST.get('quantity_of_water'+str(index)) or '').strip() or None
                    # time_of_application = (request.POST.get('time_of_application'+str(index)) or '').strip() or None
                    time_roller =""
                    mover_machine_type =""
                    mover_machinery_name_operator = ""
                    moving_passes_unit ="" 
                    mowing_duration = ""
                    roller_machine_type = ""
                    roller_machinery_name_operator =""
                    is_daily_watering = request.POST.get('is_daily_watering', 'off') == 'on'
                    is_daily_watering = "1" if request.POST.get('is_daily_watering', 'off') == 'on' else "0"
                    mover_machinery_id = ""
                    roller_machine_type = ""
                    
                    watering_entries_json = (request.POST.get("watering_entries_json"+str(index)) or '').strip() or None
                    watering_entries = json.loads(watering_entries_json) if watering_entries_json else []
                    if(len(watering_entries)>0):
                        for water in watering_entries:
                            last_watering_on+=str(water["last_watering_on"])+"__####__"
                            time_of_application+=str(water["time_of_application"])+"__####__"
                            quantity_of_water+=str(water["quantity_of_water"])+"__####__"
                           
                           
                        # print(time_of_application_chemical+"\n"+pitch_main_chemical_weight+"\n"+pitch_main_chemical_unit+"\n"+chemical_details_remark+"\n"+fertilizers_details)
                    else:
                        print("No Watering")
                    
                    # total_records = int(request.POST.get("rolling_entries_json", "0"))
                    rolling_entries_json = (request.POST.get("rolling_entries_json"+str(index)) or '').strip() or None
                    rolling_entries = json.loads(rolling_entries_json) if rolling_entries_json else []
                    if(len(rolling_entries)>0):
                        for roll in rolling_entries:
                            rolling_date+=str(roll["date"])+"__####__"
                            machinery_id+=str(roll["machineryId"])+"__####__"
                            passes_unit+=str(roll["unit"])+"__####__"
                            no_of_passes+=str(roll["passes"])+"__####__"
                            rolling_speed+=str(roll["speed"])+"__####__"
                            time_roller+=str(roll["time"])+"__####__"
                            roller_machine_type+=str(roll["machineType"])+"__####__"
                            roller_machinery_name_operator+=str(roll["operator"])+"__####__"
                            print(machinery_id+" "+passes_unit)
                        # print(time_of_application_chemical+"\n"+pitch_main_chemical_weight+"\n"+pitch_main_chemical_unit+"\n"+chemical_details_remark+"\n"+fertilizers_details)
                    else:
                        print("No Rollers")
                    date_mowing_done_last=""
                    time_of_application_mover=""
                    mowing_done_at_mm=""
                    mover_entries_json = (request.POST.get("mover_entries_json"+str(index)) or '').strip() or None
                    mover_entries = json.loads(mover_entries_json) if mover_entries_json else []
                    if(len(mover_entries)>0):
                        for mov in mover_entries:
                         

                            mover_machinery_id+=str(mov["machineryId"])+"__####__"
                            moving_passes_unit+=str(mov["unit"])+"__####__"
                            mowing_duration+=str(mov["duration"])+"__####__"
                            date_mowing_done_last+=str(mov["date"])+"__####__"
                            time_of_application_mover+=str(mov["time"])+"__####__"
                            mover_machine_type+=str(mov["type"])+"__####__"
                            mover_machinery_name_operator+=str(mov["operator"])+"__####__"
                            mowing_done_at_mm+=str(mov["mowHeight"])+"__####__"
                            print(mover_machinery_id+" "+moving_passes_unit)
                        # print(time_of_application_chemical+"\n"+pitch_main_chemical_weight+"\n"+pitch_main_chemical_unit+"\n"+chemical_details_remark+"\n"+fertilizers_details)
                    else:
                        print("No Movers")
              
                    # date_mowing_done_last = (request.POST.get('date_mowing_done_last'+str(index)) or '').strip() or None
                    # time_of_application_mover = (request.POST.get('time_of_application_mover'+str(index)) or '').strip() or None
                    # mowing_done_at_mm = (request.POST.get('mowing_done_at_mm'+str(index)) or '').strip() or None
                  
                    # is_fertilizers_used = request.POST.get('is_fertilizers_used', 'off') == 'on'
                    is_fertilizers_used = 0
                    # fertilizers_details = (request.POST.get('fertilizers_details'+str(index)) or '').strip() or None
                    fertilizers_details = ""
                    # chemical_details_remark = (request.POST.get('chemical_details_remark'+str(index)) or '').strip() or None
                    chemical_details_remark = ""
                    # time_of_application_chemical = (request.POST.get("time_of_application_chemical"+str(index)) or '').strip() or None
                    time_of_application_chemical = ""
                    # pitch_main_chemical_weight=(request.POST.get("chemical_weight"+str(index)) or '').strip() or None
                    chemical_weight=""
                    # pitch_main_chemical_unit=(request.POST.get("fertilizers_unit"+str(index)) or '').strip() or None
                    fertilizers_unit=""
                    
                    chemical_entries=(request.POST.get("chemical_entries"+str(index)) or '').strip() or None
                    chemical_entries = json.loads(chemical_entries) if chemical_entries else []
                    if(len(chemical_entries)>0):
                          is_fertilizers_used=1
                          for chem in chemical_entries:
                            time_of_application_chemical+=str(chem["time"])+"__####__"
                            chemical_weight+=str(chem["weight"])+"__####__"
                            fertilizers_unit+=str(chem["unit"])+"__####__"
                            chemical_details_remark+=str(chem["remark"])+"__####__"
                            fertilizers_details+=str(chem["chem"])+"__####__"
                            # print(time_of_application_chemical+"\n"+pitch_main_chemical_weight+"\n"+pitch_main_chemical_unit+"\n"+chemical_details_remark+"\n"+fertilizers_details)
                    else:
                        is_fertilizers_used=0
                        print("No Chemicals")
                
                else:
                    machinery_id = request.POST.get('machinery_id')
                    rolling_date=request.POST.get('rolling_date')
                    no_of_passes = request.POST.get('no_of_passes')
                    rolling_speed = request.POST.get('rolling_speed')
                    last_watering_on = request.POST.get('last_watering_on')
                    quantity_of_water = request.POST.get('quantity_of_water')
                    time_of_application = request.POST.get('time_of_application')
                    time_roller = request.POST.get('time_roller')
                    mover_machine_type = (request.POST.get('mover_machine_type'))
                    mover_machinery_name_operator = (request.POST.get('mover_machinery_name_operator'))
                    moving_passes_unit = (request.POST.get('moving_passes_unit'))
                    mowing_duration = (request.POST.get('mowing_duration'))
                    roller_machine_type = (request.POST.get('roller_machine_type'))
                    roller_machinery_name_operator = (request.POST.get('roller_machinery_name_operator'))
                    # is_daily_watering = request.POST.get('is_daily_watering', 'off') == 'on'
                    # is_daily_watering = "1" if request.POST.get('is_daily_watering', 'off') == 'on' else "0"
                    mover_machinery_id = request.POST.get('mover_machinery_id')
                    date_mowing_done_last = request.POST.get('date_mowing_done_last')
                    time_of_application_mover = request.POST.get('time_of_application_mover')
                    mowing_done_at_mm = request.POST.get('mowing_done_at_mm')
                    # is_fertilizers_used = request.POST.get('is_fertilizers_used', 'off') == 'on'
                    is_fertilizers_used = 1 if request.POST.get('is_fertilizers_used') else 0
                    fertilizers_details = request.POST.get('fertilizers_details')
                    chemical_details_remark = request.POST.get('chemical_details_remark')
                    time_of_application_chemical = request.POST.get("time_of_application_chemical")
                    chemical_weight=request.POST.get("chemical_weight")
                    fertilizers_unit=request.POST.get("fertilizers_unit")
                    passes_unit=request.POST.get("passes_unit")
                    
                remark_by_groundsman = request.POST.get('remark_by_groundsman')

                    # machinery_id = (request.POST.get('machinery_id'+str(index)) or '').strip() or None
                    # no_of_passes = (request.POST.get('no_of_passes'+str(index)) or '').strip() or None
                    # rolling_speed = (request.POST.get('rolling_speed'+str(index)) or '').strip() or None
                    # last_watering_on = (request.POST.get('last_watering_on'+str(index)) or '').strip() or None
                    # quantity_of_water = (request.POST.get('quantity_of_water'+str(index)) or '').strip() or None
                    # time_of_application = (request.POST.get('time_of_application'+str(index)) or '').strip() or None
                    # time_roller = (request.POST.get('time_roller'+str(index)) or '').strip() or None
                    # # is_daily_watering = request.POST.get('is_daily_watering', 'off') == 'on'
                    # # is_daily_watering = "1" if request.POST.get('is_daily_watering', 'off') == 'on' else "0"
                    # mover_machinery_id = (request.POST.get('mover_machinery_id'+str(index)) or '').strip() or None
                    # date_mowing_done_last = (request.POST.get('date_mowing_done_last'+str(index)) or '').strip() or None
                    # time_of_application_mover = (request.POST.get('time_of_application_mover'+str(index)) or '').strip() or None
                    # mowing_done_at_mm = (request.POST.get('mowing_done_at_mm'+str(index)) or '').strip() or None
                    # # is_fertilizers_used = request.POST.get('is_fertilizers_used', 'off') == 'on'
                    # is_fertilizers_used = "1" if request.POST.get('is_fertilizers_used'+str(index), 'off') == 'on' else "0"
                    # fertilizers_details = (request.POST.get('fertilizers_details'+str(index)) or '').strip() or None
                    # chemical_details_remark = (request.POST.get('chemical_details_remark'+str(index)) or '').strip() or None
                    # time_of_application_chemical=(request.POST.get('time_of_application_chemical'+str(index)) or '').strip() or None
                    
                    # chemical_weight=(request.POST.get('chemical_weight'+str(index)) or '').strip() or None
                    # fertilizers_unit=(request.POST.get('fertilizers_unit'+str(index)) or '').strip() or None
                    
                # else:
                    # machinery_id = request.POST.get('machinery_id')
                    # no_of_passes = request.POST.get('no_of_passes')
                    # rolling_speed = request.POST.get('rolling_speed')
                    # last_watering_on = request.POST.get('last_watering_on')
                    # quantity_of_water = request.POST.get('quantity_of_water')
                    # time_of_application = request.POST.get('time_of_application')
                    # time_roller = request.POST.get('time_roller')
                    # # is_daily_watering = request.POST.get('is_daily_watering', 'off') == 'on'
                    # # is_daily_watering = "1" if request.POST.get('is_daily_watering', 'off') == 'on' else "0"
                    # mover_machinery_id = request.POST.get('mover_machinery_id')
                    # date_mowing_done_last = request.POST.get('date_mowing_done_last')
                    # time_of_application_mover = request.POST.get('time_of_application_mover')
                    # mowing_done_at_mm = request.POST.get('mowing_done_at_mm')
                    # # is_fertilizers_used = request.POST.get('is_fertilizers_used', 'off') == 'on'
                    # is_fertilizers_used = "1" if request.POST.get('is_fertilizers_used', 'off') == 'on' else "0"
                    # fertilizers_details = request.POST.get('fertilizers_details')
                    # chemical_details_remark = request.POST.get('chemical_details_remark')
                    # time_of_application_chemical=request.POST.get('time_of_application_chemical')
                    
                    # chemical_weight=request.POST.get('chemical_weight')
                    # fertilizers_unit=request.POST.get('fertilizers_unit')
                    
                # remark_by_groundsman = request.POST.get('remark_by_groundsman')

                # Extract outfield entries
                if(outfieldIndex>0):
                    
                    print("Outfiled1")
                    print("Outfiled2")
                    # out_machinery_id = (request.POST.get('out_machinery_id'+str(index)) or '').strip() or None
                    out_machinery_id = ""
                    out_passes_unit =""
                    out_rolling_date=""
                    
                    # out_no_of_passes = (request.POST.get('out_no_of_passes'+str(index)) or '').strip() or None
                    out_no_of_passes =""
                
                    # out_rolling_speed = (request.POST.get('out_rolling_speed'+str(index)) or '').strip() or None
                    out_rolling_speed =""
                    
                    out_last_watering_on = ""
                    out_quantity_of_water = ""
                    out_time_of_application = ""
                    
                    # out_last_watering_on = (request.POST.get('out_last_watering_on'+str(index)) or '').strip() or None
                    # out_quantity_of_water = (request.POST.get('out_quantity_of_water'+str(index)) or '').strip() or None
                    # out_time_of_application = (request.POST.get('out_time_of_application'+str(index)) or '').strip() or None
                    # out_time_of_application = ""
                    # out_time_roller = (request.POST.get('out_time_roller'+str(index)) or '').strip() or None
                    out_time_roller = ""
                    # out_mover_machine_type = (request.POST.get('out_mover_machine_type'+str(index)) or '').strip() or None
                    out_mover_machine_type = ""
                    # out_mover_machinery_name_operator = (request.POST.get('out_mover_machinery_name_operator'+str(index)) or '').strip() or None
                    out_mover_machinery_name_operator = ""
                    # out_moving_passes_unit = (request.POST.get('out_moving_passes_unit'+str(index)) or '').strip() or None
                    out_moving_passes_unit = ""
                    # out_mowing_duration = (request.POST.get('out_mowing_duration'+str(index)) or '').strip() or None
                    out_mowing_duration = ""
                    # out_roller_machine_type = (request.POST.get('out_roller_machine_type'+str(index)) or '').strip() or None
                    out_roller_machine_type =""
                    # out_roller_machinery_name_operator = (request.POST.get('out_roller_machinery_name_operator'+str(index)) or '').strip() or None
                    out_roller_machinery_name_operator = ""
                    # out_is_daily_watering = request.POST.get('out_is_daily_watering', 'off') == 'on'
                    # out_is_daily_watering = "1" if request.POST.get('out_is_daily_watering', 'off') == 'on' else "0"
                    # out_mover_machinery_id = (request.POST.get('out_mover_machinery_id'+str(index)) or '').strip() or None
                    out_mover_machinery_id =""
                    # out_date_mowing_done_last = (request.POST.get('out_date_mowing_done_last'+str(index)) or '').strip() or None
                    out_date_mowing_done_last =""
                    # out_time_of_application_mover = (request.POST.get('out_time_of_application_mover'+str(index)) or '').strip() or None
                    out_time_of_application_mover =""
                    # out_mowing_done_at_mm = (request.POST.get('out_mowing_done_at_mm'+str(index)) or '').strip() or None
                    out_mowing_done_at_mm = ""
                    # out_is_fertilizers_used = request.POST.get('out_is_fertilizers_used', 'off') == 'on'
                    out_is_fertilizers_used =  0
                    # out_fertilizers_details = (request.POST.get('out_fertilizers_details'+str(index)) or '').strip() or None
                    out_fertilizers_details = ""
                    # out_chemical_details_remark = (request.POST.get('out_chemical_details_remark'+str(index)) or '').strip() or None
                    out_chemical_details_remark = ""
                    # out_time_of_application_chemical = (request.POST.get("out_time_of_application_chemical"+str(index)) or '').strip() or None
                    out_time_of_application_chemical = ""
                    # outfield_chemical_weight=(request.POST.get("out_chemical_weight"+str(index)) or '').strip() or None
                    out_chemical_weight=""
                    # outfield_chemical_unit=(request.POST.get("out_fertilizers_unit"+str(index)) or '').strip() or None
                    out_fertilizers_unit=""
                    
                    out_watering_entries_json = (request.POST.get("out_watering_entries_json"+str(index)) or '').strip() or None
                    out_watering_entries = json.loads(out_watering_entries_json) if out_watering_entries_json else []
                    if(len(out_watering_entries)>0):
                        for water in out_watering_entries:
                            out_last_watering_on+=str(water["last_watering_on"])+"__####__"
                            out_time_of_application+=str(water["time_of_application"])+"__####__"
                            out_quantity_of_water+=str(water["quantity_of_water"])+"__####__"
                           
                           
                        # print(time_of_application_chemical+"\n"+pitch_main_chemical_weight+"\n"+pitch_main_chemical_unit+"\n"+chemical_details_remark+"\n"+fertilizers_details)
                    else:
                        print("No Watering")
                    
                    out_chemical_entries=(request.POST.get("out_chemical_entries"+str(index)) or '').strip() or None
                    out_chemical_entries = json.loads(out_chemical_entries) if out_chemical_entries else []
                    if(len(out_chemical_entries)>0):
                        out_is_fertilizers_used=1
                        for chem in out_chemical_entries:
                            out_time_of_application_chemical+=str(chem["time"])+"__####__"
                            out_chemical_weight+=str(chem["weight"])+"__####__"
                            out_fertilizers_unit+=str(chem["unit"])+"__####__"
                            out_chemical_details_remark+=str(chem["remark"])+"__####__"
                            out_fertilizers_details+=str(chem["chemical"])+"__####__"
                            # print(time_of_application_chemical+"\n"+pitch_main_chemical_weight+"\n"+pitch_main_chemical_unit+"\n"+chemical_details_remark+"\n"+fertilizers_details)
                    else:
                        out_is_fertilizers_used=0
                        print("No Chemicals")
                        print("Outfiled3")
                    
                    out_rolling_entries_json = (request.POST.get("out_rolling_entries_json"+str(index)) or '').strip() or None
                    out_rolling_entries = json.loads(out_rolling_entries_json) if out_rolling_entries_json else []
                    if(len(out_rolling_entries)>0):
                        for roll in out_rolling_entries:
                            out_machinery_id+=str(roll["machineryId"])+"__####__"
                            out_rolling_date+=str(roll["date"])+"__####__"
                            out_passes_unit+=str(roll["unit"])+"__####__"
                            out_no_of_passes+=str(roll["passes"])+"__####__"
                            out_rolling_speed+=str(roll["speed"])+"__####__"
                            out_time_roller+=str(roll["time"])+"__####__"
                            out_roller_machine_type+=str(roll["machineType"])+"__####__"
                            out_roller_machinery_name_operator+=str(roll["operator"])+"__####__"
                            print(out_machinery_id+" "+out_passes_unit)
                        # print(time_of_application_chemical+"\n"+pitch_main_chemical_weight+"\n"+pitch_main_chemical_unit+"\n"+chemical_details_remark+"\n"+fertilizers_details)
                    else:
                        print("No Rollers")
                    
                    out_mover_entries_json = (request.POST.get("out_mover_entries_json"+str(index)) or '').strip() or None
                    out_mover_entries = json.loads(out_mover_entries_json) if out_mover_entries_json else []
                    if(len(out_mover_entries)>0):
                        for mov in out_mover_entries:
                         

                            out_mover_machinery_id+=str(mov["machineryId"])+"__####__"
                            out_moving_passes_unit+=str(mov["unit"])+"__####__"
                            out_mowing_duration+=str(mov["duration"])+"__####__"
                            out_date_mowing_done_last+=str(mov["date"])+"__####__"
                            out_time_of_application_mover+=str(mov["time"])+"__####__"
                            out_mover_machine_type+=str(mov["type"])+"__####__"
                            out_mover_machinery_name_operator+=str(mov["operator"])+"__####__"
                            out_mowing_done_at_mm+=str(mov["mowHeight"])+"__####__"
                            print(out_mover_machinery_id+" "+out_moving_passes_unit)
                        # print(time_of_application_chemical+"\n"+pitch_main_chemical_weight+"\n"+pitch_main_chemical_unit+"\n"+chemical_details_remark+"\n"+fertilizers_details)
                    else:
                        print("No Movers")
                
                else:
                    out_machinery_id = request.POST.get('out_machinery_id')
                    out_rolling_date = request.POST.get('out_rolling_date')
                    out_no_of_passes = request.POST.get('out_no_of_passes')
                    out_rolling_speed = request.POST.get('out_rolling_speed')
                    out_last_watering_on = request.POST.get('out_last_watering_on')
                    out_quantity_of_water = request.POST.get('out_quantity_of_water')
                    out_time_of_application = request.POST.get('out_time_of_application')
                    out_time_roller = request.POST.get('out_time_roller')
                    out_mover_machine_type = (request.POST.get('out_mover_machine_type'))
                    out_mover_machinery_name_operator = (request.POST.get('out_mover_machinery_name_operator'))
                    out_moving_passes_unit = (request.POST.get('out_moving_passes_unit'))
                    out_mowing_duration = (request.POST.get('out_mowing_duration'))
                    out_roller_machine_type = (request.POST.get('out_roller_machine_type'))
                    out_roller_machinery_name_operator = (request.POST.get('out_roller_machinery_name_operator'))
                    # out_is_daily_watering = request.POST.get('out_is_daily_watering', 'off') == 'on'
                    # out_is_daily_watering = "1" if request.POST.get('out_is_daily_watering', 'off') == 'on' else "0"
                    out_mover_machinery_id = request.POST.get('out_mover_machinery_id')
                    out_date_mowing_done_last = request.POST.get('out_date_mowing_done_last')
                    out_time_of_application_mover = request.POST.get('out_time_of_application_mover')
                    out_mowing_done_at_mm = request.POST.get('out_mowing_done_at_mm')
                    # out_is_fertilizers_used = request.POST.get('out_is_fertilizers_used', 'off') == 'on'
                    out_is_fertilizers_used = 1 if request.POST.get('out_is_fertilizers_used') else 0
                    out_fertilizers_details = request.POST.get('out_fertilizers_details')
                    out_chemical_details_remark = request.POST.get('out_chemical_details_remark')
                    out_time_of_application_chemical = request.POST.get("out_time_of_application_chemical")
                    out_chemical_weight=request.POST.get("out_chemical_weight")
                    out_fertilizers_unit=request.POST.get("out_fertilizers_unit")
                    out_passes_unit=request.POST.get("out_passes_unit")
                    
                out_remark_by_groundsman = request.POST.get('out_remark_by_groundsman')
                  
               
                #     out_machinery_id = (request.POST.get('out_machinery_id'+str(index)) or '').strip() or None
                #     out_no_of_passes = (request.POST.get('out_no_of_passes'+str(index)) or '').strip() or None
                #     out_rolling_speed = (request.POST.get('out_rolling_speed'+str(index)) or '').strip() or None
                #     out_last_watering_on = (request.POST.get('out_last_watering_on'+str(index)) or '').strip() or None
                #     out_quantity_of_water = (request.POST.get('out_quantity_of_water'+str(index)) or '').strip() or None
                #     out_time_of_application = (request.POST.get('out_time_of_application'+str(index)) or '').strip() or None
                #     out_time_roller = (request.POST.get('out_time_roller'+str(index)) or '').strip() or None
                #     # out_is_daily_watering = request.POST.get('out_is_daily_watering', 'off') == 'on'
                #     # out_is_daily_watering = "1" if request.POST.get('out_is_daily_watering', 'off') == 'on' else "0"
                #     out_mover_machinery_id = (request.POST.get('out_mover_machinery_id'+str(index)) or '').strip() or None
                #     out_date_mowing_done_last = (request.POST.get('out_date_mowing_done_last'+str(index)) or '').strip() or None
                #     out_time_of_application_mover = (request.POST.get('out_time_of_application_mover'+str(index)) or '').strip() or None
                #     out_mowing_done_at_mm = (request.POST.get('out_mowing_done_at_mm'+str(index)) or '').strip() or None
                #     # out_is_fertilizers_used = request.POST.get('out_is_fertilizers_used', 'off') == 'on'
                #     out_is_fertilizers_used = "1" if request.POST.get('out_is_fertilizers_used'+str(index), 'off') == 'on' else "0"
                #     out_fertilizers_details = (request.POST.get('out_fertilizers_details'+str(index)) or '').strip() or None
                #     out_chemical_details_remark = (request.POST.get('out_chemical_details_remark'+str(index)) or '').strip() or None
                #     out_time_of_application_chemical=(request.POST.get('out_time_of_application_chemical'+str(index)) or '').strip() or None
                #     out_chemical_weight=(request.POST.get('out_chemical_weight'+str(index)) or '').strip() or None
                #     out_fertilizers_unit=(request.POST.get('out_fertilizers_unit'+str(index)) or '').strip() or None
                    
                # else:
                #     out_machinery_id = request.POST.get('out_machinery_id')
                #     out_no_of_passes = request.POST.get('out_no_of_passes')
                #     out_rolling_speed = request.POST.get('out_rolling_speed')
                #     out_last_watering_on = request.POST.get('out_last_watering_on')
                #     out_quantity_of_water = request.POST.get('out_quantity_of_water')
                #     out_time_of_application = request.POST.get('out_time_of_application')
                #     out_time_roller = request.POST.get('out_time_roller')
                #     # out_is_daily_watering = request.POST.get('out_is_daily_watering', 'off') == 'on'
                #     # out_is_daily_watering = "1" if request.POST.get('out_is_daily_watering', 'off') == 'on' else "0"
                #     out_mover_machinery_id = request.POST.get('out_mover_machinery_id')
                #     out_date_mowing_done_last = request.POST.get('out_date_mowing_done_last')
                #     out_time_of_application_mover = request.POST.get('out_time_of_application_mover')
                #     out_mowing_done_at_mm = request.POST.get('out_mowing_done_at_mm')
                #     # out_is_fertilizers_used = request.POST.get('out_is_fertilizers_used', 'off') == 'on'
                #     out_is_fertilizers_used = "1" if request.POST.get('out_is_fertilizers_used', 'off') == 'on' else "0"
                #     out_fertilizers_details = request.POST.get('out_fertilizers_details')
                #     out_chemical_details_remark = request.POST.get('out_chemical_details_remark')
                #     out_time_of_application_chemical=request.POST.get('out_time_of_application_chemical')
                #     out_chemical_weight=request.POST.get('out_chemical_weight')
                #     out_fertilizers_unit=request.POST.get('out_fertilizers_unit')
                    
                # out_remark_by_groundsman = request.POST.get('out_remark_by_groundsman')
                brief_match_pitch_assessment = request.POST.get('brief_match_pitch_assessment')
                
            
                # Insert data
                with connection.cursor() as cursor:
                    sql=f'''INSERT INTO {org_id}_match_master 
                            (match_type, name_tournament, team1, team2,dew_factor,access_bounce, 
                            preparation_date, match_date, from_date, to_date,
                            days_count, start_time, pitch_id, ground_id, is_pitch_level, lawn_height, 
                            grass_cover, 
                            min_temp, max_temp, forecast, moisture_upto,  
                            
                            machinery_id, no_of_passes, 
                            rolling_speed, last_watering_on,
                            quantity_of_water, time_of_application,time_roller,out_time_roller,
                            mover_machinery_id, date_mowing_done_last, time_of_application_mover, 
                            mowing_done_at_mm, 
                            is_fertilizers_used, fertilizers_details, chemical_details_remark, 
                            remark_by_groundsman, 
                            out_machinery_id, out_no_of_passes, out_rolling_speed, out_last_watering_on, 
                            out_quantity_of_water, 
                            out_time_of_application, out_mover_machinery_id, out_date_mowing_done_last, 
                            time_of_application_out_mover, out_mowing_done_at_mm, out_is_fertilizers_used,
                            out_fertilizers_details, 
                            out_chemical_details_remark, out_remark_by_groundsman, 
                            brief_match_pitch_assessment,time_of_application_chemical,out_time_of_application_chemical,
                            chemical_weight,fertilizers_unit,
                            out_chemical_weight,out_fertilizers_unit,nuteral_curator,
                            
                            out_mover_machine_type,
                            out_mover_machinery_name_operator, 
                            out_moving_passes_unit, 
                            out_mowing_duration,
                            
                            mover_machine_type , 
                            mover_machinery_name_operator ,
                            moving_passes_unit, 
                            mowing_duration,
                            
                            roller_machine_type,
                            roller_machinery_name_operator,
                            out_roller_machine_type,
                            out_roller_machinery_name_operator,
                            passes_unit,
                            out_passes_unit,
                            rolling_date,
                            out_rolling_date
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
    %s, %s,%s,%s,%s, %s,%s,%s,%s,%s,%s,%s,%s, %s,%s,%s,%s,%s,%s, %s,%s,%s,%s,%s,%s)'''
                    
                    values=[
                        match_type, name_tournament, team1, team2,dew_factor, access_bounce,preparation_date, match_date, from_date, to_date,
                        days_count, start_time, pitch_id, ground_id, is_pitch_level, lawn_height, grass_cover,
                        min_temp, max_temp, forecast, moisture_upto,  machinery_id, no_of_passes, rolling_speed, 
                        last_watering_on, quantity_of_water, time_of_application,time_roller,out_time_roller,
                        mover_machinery_id, date_mowing_done_last, time_of_application_mover,
                        mowing_done_at_mm,
                        is_fertilizers_used, fertilizers_details, chemical_details_remark, remark_by_groundsman,
                        out_machinery_id, out_no_of_passes, out_rolling_speed, out_last_watering_on, out_quantity_of_water,
                        out_time_of_application, out_mover_machinery_id, out_date_mowing_done_last,
                        out_time_of_application_mover, out_mowing_done_at_mm, out_is_fertilizers_used,
                        out_fertilizers_details,
                        out_chemical_details_remark, out_remark_by_groundsman,
                        brief_match_pitch_assessment,time_of_application_chemical,
                        out_time_of_application_chemical,
                        chemical_weight,fertilizers_unit,
                        out_chemical_weight,out_fertilizers_unit,nuteral_curator,
                         out_mover_machine_type,
                            out_mover_machinery_name_operator, 
                            out_moving_passes_unit, 
                            out_mowing_duration,
                            
                            mover_machine_type , 
                            mover_machinery_name_operator ,
                            moving_passes_unit, 
                            mowing_duration,
                            
                            roller_machine_type,
                            roller_machinery_name_operator,
                            out_roller_machine_type,
                            out_roller_machinery_name_operator,
                            passes_unit,
                            out_passes_unit,
                            rolling_date,
                            out_rolling_date

                    ]
                    # print(sql)
                    # print(values)
                    cursor.execute(sql,values)

            return redirect('match_list')

        return render(request, 'admin_user/match_master.html')
    except Exception as e:
        print(e)
        return HttpResponse(e)


def update_match(request, match_id):
    try:
        org_id = request.session["org_id"]

        # Fetch match data to pre-populate the form
        with connection.cursor() as cursor:
            cursor.execute(f'SELECT * FROM {org_id}_match_master WHERE id = %s', [match_id])
            match = cursor.fetchone()

        if not match:
            raise Exception("Match not found")

        if request.method == 'POST':
            # Collecting data from the form
            match_type = request.POST.get('match_type')
            name_tournament = request.POST.get('name_tournament')
            team1 = request.POST.get('team1')
            team2 = request.POST.get('team2')
            preparation_date = request.POST.get('preparation_date')
            match_date = request.POST.get('match_date')
            from_date = request.POST.get('from_date')
            to_date = request.POST.get('to_date')
            days_count = request.POST.get('days_count')
            start_time = request.POST.get('start_time')
            nuteral_curator =request.POST.get('nuteral_curator')
            
            # pitch_id = request.POST.get('pitch_id') if request.POST.get('pitch_id') else ""
            pitch_id_text = request.POST.get('pitch_id_text')
            # ground_id = request.POST.get('ground_id')
            ground_id_text = request.POST.get('ground_id_text')
            # print(pitch_id, ground_id)
            # print(pitch_id_text, ground_id_text)
            is_pitch_level = request.POST.get('is_pitch_level', 'off') == 'on'
            lawn_height = request.POST.get('lawn_height')
            grass_cover = request.POST.get('grass_cover')
            min_temp = request.POST.get('min_temp')
            max_temp = request.POST.get('max_temp')
            forecast = request.POST.get('forecast')
            moisture_upto = request.POST.get('moisture_upto')
            dew_factor =request.POST.get('dew_factor')
            access_bounce =request.POST.get('access_bounce')
            # rolling_time = request.POST.get('rolling_time')
            # rolling_pattern = request.POST.get('rolling_pattern')
            machinery_id = request.POST.get('machinery_id')
            no_of_passes = request.POST.get('no_of_passes')
            rolling_speed = request.POST.get('rolling_speed')
            last_watering_on = request.POST.get('last_watering_on')
            quantity_of_water = request.POST.get('quantity_of_water')
            time_of_application = request.POST.get('time_of_application')
            time_roller = request.POST.get('time_roller')
            machinery_id = ""
            no_of_passes = ""
            rolling_speed = ""
            last_watering_on = ""
            quantity_of_water = ""
            time_of_application = ""
            time_roller = ""
            # is_daily_watering = request.POST.get('is_daily_watering', 'off') == 'on'
            # is_daily_watering = "1" if request.POST.get('is_daily_watering', 'off') == 'on' else "0"
            mover_machinery_id = ""
            date_mowing_done_last = ""
            time_of_application_mover = ""
            mowing_done_at_mm = ""
            # is_fertilizers_used = request.POST.get('is_fertilizers_used', 'off') == 'on'
            is_fertilizers_used = 0
            fertilizers_details = ""
            chemical_details_remark = ""
            remark_by_groundsman = ""
            time_of_application_chemical = ""
            out_time_of_application_chemical = ""
            pitch_main_chemical_weight=""
            pitch_main_chemical_unit=""
            outfield_chemical_weight=""
            outfield_chemical_unit=""
           
            
            #main
            passes_unit = ""
            roller_machine_type = ""
            roller_machinery_name_operator =""
            mover_machine_type =""
            mover_machinery_name_operator = ""
            moving_passes_unit ="" 
            mowing_duration = ""
            
            #outfield
            out_passes_unit =""
            out_mover_machine_type = ""
            out_mover_machinery_name_operator = ""
            out_moving_passes_unit = ""
            out_mowing_duration = ""
            out_roller_machine_type =""
            out_roller_machinery_name_operator = "" 
            rolling_date=""
            
            watering_entries_json = (request.POST.get("watering_entries_json") or '').strip() or None
            watering_entries = json.loads(watering_entries_json) if watering_entries_json else []
            if(len(watering_entries)>0):
                for water in watering_entries:
                    last_watering_on+=str(water["last_watering_on"])+"__####__"
                    time_of_application+=str(water["time_of_application"])+"__####__"
                    quantity_of_water+=str(water["quantity_of_water"])+"__####__"
            
            rolling_entries_json = (request.POST.get("rolling_entries_json") or '').strip() or None
            rolling_entries = json.loads(rolling_entries_json) if rolling_entries_json else []
            if(len(rolling_entries)>0):
                for roll in rolling_entries:
                    rolling_date+=str(roll["date"])+"__####__"
                    machinery_id+=str(roll["machineryId"])+"__####__"
                    passes_unit+=str(roll["unit"])+"__####__"
                    no_of_passes+=str(roll["passes"])+"__####__"
                    rolling_speed+=str(roll["speed"])+"__####__"
                    time_roller+=str(roll["time"])+"__####__"
                    roller_machine_type+=str(roll["machineType"])+"__####__"
                    roller_machinery_name_operator+=str(roll["operator"])+"__####__"
                    print("main",machinery_id+" "+passes_unit)
                    # print(time_of_application_chemical+"\n"+pitch_main_chemical_weight+"\n"+pitch_main_chemical_unit+"\n"+chemical_details_remark+"\n"+fertilizers_details)
            else:
                print("No Rollers")
                
            mover_entries_json = (request.POST.get("mover_entries_json") or '').strip() or None
            mover_entries = json.loads(mover_entries_json) if mover_entries_json else []
            if(len(mover_entries)>0):
                for mov in mover_entries:
                    mover_machinery_id+=str(mov["machineryId"])+"__####__"
                    moving_passes_unit+=str(mov["unit"])+"__####__"
                    mowing_duration+=str(mov["duration"])+"__####__"
                    date_mowing_done_last+=str(mov["date"])+"__####__"
                    time_of_application_mover+=str(mov["time"])+"__####__"
                    mover_machine_type+=str(mov["type"])+"__####__"
                    mover_machinery_name_operator+=str(mov["operator"])+"__####__"
                    mowing_done_at_mm+=str(mov["mowHeight"])+"__####__"
                    print(mover_machinery_id+" "+moving_passes_unit)
                    # print(time_of_application_chemical+"\n"+pitch_main_chemical_weight+"\n"+pitch_main_chemical_unit+"\n"+chemical_details_remark+"\n"+fertilizers_details)
            else:
                print("No Movers")
            
            chemical_entries=(request.POST.get("chemical_entries") or '').strip() or None
            chemical_entries = json.loads(chemical_entries) if chemical_entries else []
            if(len(chemical_entries)>0):
                is_fertilizers_used=1
                for chem in chemical_entries:
                    time_of_application_chemical+=str(chem["time"])+"__####__"
                    pitch_main_chemical_weight+=str(chem["weight"])+"__####__"
                    pitch_main_chemical_unit+=str(chem["unit"])+"__####__"
                    chemical_details_remark+=str(chem["remark"])+"__####__"
                    fertilizers_details+=str(chem["chem"])+"__####__"
                    # print(time_of_application_chemical+"\n"+pitch_main_chemical_weight+"\n"+pitch_main_chemical_unit+"\n"+chemical_details_remark+"\n"+fertilizers_details)
            else:
                is_fertilizers_used=0
                print("No Chemicals")
            
            
            out_machinery_id = ""
            out_no_of_passes = ""
            out_rolling_speed = ""
            out_last_watering_on = ""
            out_quantity_of_water = ""
            out_time_of_application = ""
           
            out_time_roller = ""
            # out_is_daily_watering = request.POST.get('out_is_daily_watering', 'off') == 'on'
            # out_is_daily_watering = "1" if request.POST.get('out_is_daily_watering', 'off') == 'on' else "0"
            out_mover_machinery_id = ""
            out_date_mowing_done_last = ""
            out_time_of_application_mover = ""
            out_mowing_done_at_mm = ""
            # out_is_fertilizers_used = request.POST.get('out_is_fertilizers_used', 'off') == 'on'
            out_is_fertilizers_used =  0
            out_fertilizers_details = ""
            out_chemical_details_remark = ""
            out_remark_by_groundsman = ""
            out_rolling_date=""
            
            out_watering_entries_json = (request.POST.get("out_watering_entries_json") or '').strip() or None
            out_watering_entries = json.loads(out_watering_entries_json) if out_watering_entries_json else []
            if(len(out_watering_entries)>0):
                for water in out_watering_entries:
                    out_last_watering_on+=str(water["last_watering_on"])+"__####__"
                    out_time_of_application+=str(water["time_of_application"])+"__####__"
                    out_quantity_of_water+=str(water["quantity_of_water"])+"__####__"
                           
            
            out_rolling_entries_json = (request.POST.get("out_rolling_entries_json") or '').strip() or None
            out_rolling_entries = json.loads(out_rolling_entries_json) if out_rolling_entries_json else []
            if(len(out_rolling_entries)>0):
                for roll in out_rolling_entries:
                    out_rolling_date+=str(roll["date"])+"__####__"
                    out_machinery_id+=str(roll["machineryId"])+"__####__"
                    out_passes_unit+=str(roll["unit"])+"__####__"
                    out_no_of_passes+=str(roll["passes"])+"__####__"
                    out_rolling_speed+=str(roll["speed"])+"__####__"
                    out_time_roller+=str(roll["time"])+"__####__"
                    out_roller_machine_type+=str(roll["machineType"])+"__####__"
                    out_roller_machinery_name_operator+=str(roll["operator"])+"__####__"
                    print("out 1",out_machinery_id+" "+out_passes_unit)
                    # print(time_of_application_chemical+"\n"+pitch_main_chemical_weight+"\n"+pitch_main_chemical_unit+"\n"+chemical_details_remark+"\n"+fertilizers_details)
            else:
                    print("No Rollers")
                    
            out_mover_entries_json = (request.POST.get("out_mover_entries_json") or '').strip() or None
            out_mover_entries = json.loads(out_mover_entries_json) if out_mover_entries_json else []
            print("out_mover_entries ",out_mover_entries)
            if(len(out_mover_entries)>0):
                for mov in out_mover_entries:
                    out_mover_machinery_id+=str(mov["machineryId"])+"__####__"
                    out_moving_passes_unit+=str(mov["unit"])+"__####__"
                    out_mowing_duration+=str(mov["duration"])+"__####__"
                    out_date_mowing_done_last+=str(mov["date"])+"__####__"
                    out_time_of_application_mover+=str(mov["time"])+"__####__"
                    out_mover_machine_type+=str(mov["type"])+"__####__"
                    out_mover_machinery_name_operator+=str(mov["operator"])+"__####__"
                    out_mowing_done_at_mm+=str(mov["mowHeight"])+"__####__"
                    print("out 2",out_mover_machinery_id+" "+out_moving_passes_unit)
                    # print(time_of_application_chemical+"\n"+pitch_main_chemical_weight+"\n"+pitch_main_chemical_unit+"\n"+chemical_details_remark+"\n"+fertilizers_details)
            else:
                print("No Movers")
            # Extract outfield entries
            
            out_chemical_entries=(request.POST.get("out_chemical_entries") or '').strip() or None
            out_chemical_entries = json.loads(out_chemical_entries) if out_chemical_entries else []
            print("out_chemical_entries ",out_chemical_entries)
            if(len(out_chemical_entries)>0):
                out_is_fertilizers_used=1
                for chem in out_chemical_entries:
                    out_time_of_application_chemical+=str(chem["time"])+"__####__"
                    outfield_chemical_weight+=str(chem["weight"])+"__####__"
                    outfield_chemical_unit+=str(chem["unit"])+"__####__"
                    out_chemical_details_remark+=str(chem["remark"])+"__####__"
                    out_fertilizers_details+=str(chem["chemical"])+"__####__"
                    # print(time_of_application_chemical+"\n"+pitch_main_chemical_weight+"\n"+pitch_main_chemical_unit+"\n"+chemical_details_remark+"\n"+fertilizers_details)
            else:
                out_is_fertilizers_used=0
                print("No Chemicals")
                print("Outfiled3")
            
            
            btnSubmit=request.POST.get("btnSubmit")
            brief_match_pitch_assessment=request.POST.get("brief_match_pitch_assessment")
            
            # Update the match record in the database
            with connection.cursor() as cursor:
                if(btnSubmit=="update"):
                    sql = f'''
                        UPDATE {org_id}_match_master 
                        SET 
                        match_type=%s, 
                        name_tournament=%s, 
                        team1=%s, 
                        team2=%s,
                        dew_factor=%s,
                        access_bounce=%s, 
                            preparation_date=%s,
                              match_date=%s, 
                            nuteral_curator=%s, 
                              from_date=%s, 
                              to_date=%s,
                            days_count=%s,
                              start_time=%s, 
                              pitch_id=%s,
                                ground_id=%s, 
                                is_pitch_level=%s, 
                                lawn_height=%s, 
                            grass_cover=%s, 
                            min_temp=%s, 
                            max_temp=%s, 
                            forecast=%s,
                              moisture_upto=%s,  
                              machinery_id=%s, 
                              no_of_passes=%s, 
                            rolling_speed=%s, 
                            last_watering_on=%s,
                                quantity_of_water=%s, 
                                time_of_application=%s,
                                time_roller=%s,
                                out_time_roller=%s,
                            mover_machinery_id=%s,
                              date_mowing_done_last=%s, 
                              time_of_application_mover=%s, 
                            mowing_done_at_mm=%s, 
                            is_fertilizers_used=%s,
                              fertilizers_details=%s,
                                chemical_details_remark=%s, 
                            remark_by_groundsman=%s, 
                            out_machinery_id=%s,
                              out_no_of_passes=%s, 
                              out_rolling_speed=%s, 
                              out_last_watering_on=%s, 
                            out_quantity_of_water=%s, 
                            out_time_of_application=%s, 
                            out_mover_machinery_id=%s, 
                            out_date_mowing_done_last=%s, 
                            time_of_application_out_mover=%s, 
                            out_mowing_done_at_mm=%s, 
                            out_is_fertilizers_used=%s,
                            out_fertilizers_details=%s, 
                            out_chemical_details_remark=%s, 
                            out_remark_by_groundsman=%s, 
                           
                            brief_match_pitch_assessment=%s,
                             time_of_application_chemical=%s,
                        out_time_of_application_chemical=%s,
                        fertilizers_unit=%s,
                        out_fertilizers_unit=%s, 
                        chemical_weight=%s, 
                        out_chemical_weight=%s,
            out_mover_machine_type=%s,
                            out_mover_machinery_name_operator=%s, 
                            out_moving_passes_unit=%s, 
                            out_mowing_duration=%s,
                            
                            mover_machine_type=%s , 
                            mover_machinery_name_operator=%s ,
                            moving_passes_unit=%s, 
                            mowing_duration=%s,
                            
                            roller_machine_type=%s,
                            roller_machinery_name_operator=%s,
                            out_roller_machine_type=%s,
                            out_roller_machinery_name_operator=%s,
                            passes_unit=%s,
                            out_passes_unit=%s,
                            rolling_date=%s,
                            out_rolling_date=%s
                        WHERE id=%s
                    '''
                    values = [
                    match_type, name_tournament, team1, team2,dew_factor, access_bounce,preparation_date, match_date,nuteral_curator, from_date, to_date,
                        days_count, start_time, pitch_id_text, ground_id_text, is_pitch_level, lawn_height, grass_cover,
                        min_temp, max_temp, forecast, moisture_upto,  machinery_id, no_of_passes, rolling_speed, 
                        last_watering_on, quantity_of_water, time_of_application,time_roller,out_time_roller,
                        mover_machinery_id, date_mowing_done_last, time_of_application_mover,
                        mowing_done_at_mm,
                        is_fertilizers_used, fertilizers_details, chemical_details_remark, remark_by_groundsman,
                        out_machinery_id, out_no_of_passes, out_rolling_speed, out_last_watering_on, out_quantity_of_water,
                        out_time_of_application, out_mover_machinery_id, out_date_mowing_done_last,
                        out_time_of_application_mover, out_mowing_done_at_mm, out_is_fertilizers_used,
                        out_fertilizers_details,
                        out_chemical_details_remark, out_remark_by_groundsman,
                       
                        brief_match_pitch_assessment,
                        time_of_application_chemical,
                        out_time_of_application_chemical,
                         pitch_main_chemical_unit, 
                         outfield_chemical_unit, 
                         pitch_main_chemical_weight,
                         outfield_chemical_weight,
                        
 out_mover_machine_type,
                            out_mover_machinery_name_operator, 
                            out_moving_passes_unit, 
                            out_mowing_duration,
                            
                            mover_machine_type , 
                            mover_machinery_name_operator ,
                            moving_passes_unit, 
                            mowing_duration,
                            
                            roller_machine_type,
                            roller_machinery_name_operator,
                            out_roller_machine_type,
                            out_roller_machinery_name_operator,
                            passes_unit,
                            out_passes_unit,
                            rolling_date,
                            out_rolling_date,
                        match_id
                    ]
                
                elif(btnSubmit=="save"):
                    sql=f'''INSERT INTO {org_id}_match_master 
                          (
                        match_type, 
                        name_tournament, 
                        team1, 
                        team2,
                        dew_factor,
                        access_bounce, 
                            preparation_date,
                              match_date, 
                            nuteral_curator, 
                              from_date, 
                              to_date,
                            days_count,
                              start_time, 
                              pitch_id,
                                ground_id, 
                                is_pitch_level, 
                                lawn_height, 
                            grass_cover, 
                            min_temp, 
                            max_temp, 
                            forecast,
                              moisture_upto,  
                              machinery_id, 
                              no_of_passes, 
                            rolling_speed, 
                            last_watering_on,
                                quantity_of_water, 
                                time_of_application,
                                time_roller,
                                out_time_roller,
                            mover_machinery_id,
                              date_mowing_done_last, 
                              time_of_application_mover, 
                            mowing_done_at_mm, 
                            is_fertilizers_used,
                              fertilizers_details,
                                chemical_details_remark, 
                            remark_by_groundsman, 
                            out_machinery_id,
                              out_no_of_passes, 
                              out_rolling_speed, 
                              out_last_watering_on, 
                            out_quantity_of_water, 
                            out_time_of_application, 
                            out_mover_machinery_id, 
                            out_date_mowing_done_last, 
                            time_of_application_out_mover, 
                            out_mowing_done_at_mm, 
                            out_is_fertilizers_used,
                            out_fertilizers_details, 
                            out_chemical_details_remark, 
                            out_remark_by_groundsman, 
                           
                            brief_match_pitch_assessment,
                             time_of_application_chemical,
                        out_time_of_application_chemical,
                        fertilizers_unit,
                        out_fertilizers_unit, 
                        chemical_weight, 
                        out_chemical_weight,
            out_mover_machine_type,
                            out_mover_machinery_name_operator, 
                            out_moving_passes_unit, 
                            out_mowing_duration,
                            
                            mover_machine_type , 
                            mover_machinery_name_operator ,
                            moving_passes_unit, 
                            mowing_duration,
                            
                            roller_machine_type,
                            roller_machinery_name_operator,
                            out_roller_machine_type,
                            out_roller_machinery_name_operator,
                            passes_unit,
                            out_passes_unit,
                            rolling_date,
                            out_rolling_date
                      
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
                          %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,%s, %s)'''
                    values = [ 
                              match_type, 
                              name_tournament, 
                              team1, 
                              team2,
                              dew_factor, 
                              access_bounce,
                              preparation_date, 
                              match_date,
                              nuteral_curator,
                              from_date, 
                              to_date,
                        days_count, 
                        start_time, 
                        pitch_id_text, 
                        ground_id_text, 
                        is_pitch_level, 
                        lawn_height, 
                        grass_cover,
                        min_temp, 
                        max_temp, 
                        forecast, 
                        moisture_upto,  
                        machinery_id, 
                        no_of_passes, 
                        rolling_speed, 
                        last_watering_on,
                        quantity_of_water, 
                        time_of_application,
                        time_roller,
                        out_time_roller,
                        mover_machinery_id, 
                        date_mowing_done_last, 
                        time_of_application_mover,
                        mowing_done_at_mm,
                        is_fertilizers_used, 
                        fertilizers_details,
                        chemical_details_remark,
                        remark_by_groundsman,
                        out_machinery_id, 
                        out_no_of_passes, 
                        out_rolling_speed, 
                        out_last_watering_on, 
                        out_quantity_of_water,
                        out_time_of_application, 
                        out_mover_machinery_id, 
                        out_date_mowing_done_last,
                        out_time_of_application_mover,
                        out_mowing_done_at_mm, 
                        out_is_fertilizers_used,
                        out_fertilizers_details,
                        out_chemical_details_remark, 
                        out_remark_by_groundsman,
                        brief_match_pitch_assessment,
                        time_of_application_chemical,
                        out_time_of_application_chemical,
                         pitch_main_chemical_unit, 
                         outfield_chemical_unit, 
                         pitch_main_chemical_weight,
                         outfield_chemical_weight,
                             out_mover_machine_type,
                            out_mover_machinery_name_operator, 
                            out_moving_passes_unit, 
                            out_mowing_duration,
                            mover_machine_type , 
                            mover_machinery_name_operator ,
                            moving_passes_unit, 
                            mowing_duration,
                            roller_machine_type,
                            roller_machinery_name_operator,
                            out_roller_machine_type,
                            out_roller_machinery_name_operator,
                            passes_unit,
                            out_passes_unit,
                            rolling_date,
                            out_rolling_date
                      
                    ]
                
                print(sql)
                cursor.execute(sql, values)

            return redirect('match_list')

        # Pass match data to the form for editing
        return render(request, 'admin_user/match_update_master.html', {'match': match})

    except Exception as e:
        print("Error:", e)
        return render(request, 'admin_user/error.html', {'error': str(e)})


@csrf_exempt
def delete_match(request,match_id):
    org_id = request.session["org_id"]
   
    with connection.cursor() as cursor:
            # Delete score by id
            cursor.execute(f"""DELETE FROM {org_id}_match_master  WHERE id = %s""", [match_id])

    return JsonResponse({'status': 'success'})


def match_list_filter(request):
    try:
        org_id = request.session["org_id"]
        ground_id = request.GET.get("ground_id")
        with connection.cursor() as cursor:
            cursor.execute(f'''SELECT `cdr`.`id`,
			`cdr`.`match_type`,
			`cdr`.`name_tournament`,
			`cdr`.`team1`,
			`cdr`.`team2`,
			`cdr`.`preparation_date`,
			`cdr`.`match_date`,
			`cdr`.`from_date`,
			`cdr`.`to_date`,
			`cdr`.`days_count`,
			`cdr`.`start_time`,
			`cdr`.`pitch_id`,
			`cdr`.`ground_id`,
			`cdr`.`is_pitch_level`,
			`cdr`.`lawn_height`,
			`cdr`.`grass_cover`,
			`cdr`.`min_temp`,
			`cdr`.`max_temp`,
			`cdr`.`forecast`,
			`cdr`.`moisture_upto`,
			`cdr`.`dew_factor`,
			`cdr`.`access_bounce`,
			`cdr`.`machinery_id`,
			`cdr`.`no_of_passes`,
			`cdr`.`rolling_speed`,
			`cdr`.`last_watering_on`,
			`cdr`.`quantity_of_water`,
			`cdr`.`time_of_application`,
			`cdr`.`time_roller`,
			`cdr`.`is_daily_watering`,
			`cdr`.`mover_machinery_id`,
			`cdr`.`date_mowing_done_last`,
			`cdr`.`time_of_application_mover`,
			`cdr`.`mowing_done_at_mm`,
			`cdr`.`is_fertilizers_used`,
			`cdr`.`fertilizers_details`,
			`cdr`.`chemical_details_remark`,
			`cdr`.`remark_by_groundsman`,
			`cdr`.`out_machinery_id`,
			`cdr`.`out_no_of_passes`,
			`cdr`.`out_rolling_speed`,
			`cdr`.`out_last_watering_on`,
			`cdr`.`out_quantity_of_water`,
			`cdr`.`out_time_of_application`,
			`cdr`.`out_time_roller`,
			`cdr`.`out_is_daily_watering`,
			`cdr`.`out_mover_machinery_id`,
			`cdr`.`out_date_mowing_done_last`,
			`cdr`.`time_of_application_out_mover`,
			`cdr`.`out_mowing_done_at_mm`,
			`cdr`.`out_is_fertilizers_used`,
			`cdr`.`out_fertilizers_details`,
			`cdr`.`out_chemical_details_remark`,
			`cdr`.`out_remark_by_groundsman`,
			`cdr`.`brief_match_pitch_assessment`,
			`cdr`.`time_of_application_chemical`,
			`cdr`.`out_time_of_application_chemical`,
			`cdr`.`created_at`,
			`cdr`.`updated_at`,
			`cdr`.`chemical_weight`,
			`cdr`.`fertilizers_unit`,
			`cdr`.`out_chemical_weight`,
			`cdr`.`out_fertilizers_unit`,
			`cdr`.`nuteral_curator`,
			`cdr`.`out_mover_machine_type`,
			`cdr`.`out_mover_machinery_name_operator`,
			`cdr`.`out_moving_passes_unit`,
			`cdr`.`out_mowing_duration`,
			`cdr`.`mover_machine_type`,
			`cdr`.`mover_machinery_name_operator`,
			`cdr`.`moving_passes_unit`,
			`cdr`.`mowing_duration`,
			`cdr`.`roller_machine_type`,
			`cdr`.`roller_machinery_name_operator`,
			`cdr`.`out_roller_machine_type`,
			`cdr`.`out_roller_machinery_name_operator`,
			`cdr`.`passes_unit`,
			`cdr`.`out_passes_unit`,
			g.ground_name,
			p.pitch_type, 
			p.pitch_placement, 
			c1.chemical_name as chem1,
			c2.chemical_name as chem2,
			m1.print_details as mch1,
			m2.print_details as mch2,
			m3.print_details as mch3,
			m4.print_details as mch4,
   `cdr`.`rolling_date`,
   `cdr`.`out_rolling_date`
	FROM {org_id}_match_master cdr
							INNER JOIN 
								{org_id}_pitch_master p ON cdr.pitch_id = p.id
							INNER JOIN 
								{org_id}_ground_master g ON cdr.ground_id = g.id
							LEFT JOIN 
								{org_id}_machinery_master m1 ON cdr.machinery_id = m1.id
							LEFT JOIN 
								{org_id}_machinery_master m2 ON cdr.mover_machinery_id = m2.id
							LEFT JOIN 
								{org_id}_machinery_master m3 ON cdr.out_machinery_id = m3.id
							LEFT JOIN 
								{org_id}_machinery_master m4 ON cdr.out_mover_machinery_id = m4.id
							LEFT JOIN 
								`{org_id}_fertilizer_master` c1 ON cdr.fertilizers_details = c1.id
							LEFT JOIN 
								`{org_id}_fertilizer_master` c2 ON cdr.out_fertilizers_details = c2.id
						   where cdr.ground_id=%s order by cdr.created_at desc''',[ground_id])
           		 
                
            matches = cursor.fetchall()


        return render(request, 'admin_user/match_list.html', {'matches': matches})
    except Exception as e:
        print(e)


def match_list(request):
    try:
        org_id = request.session["org_id"]
        user = request.session.get("user")
        print("user is:",user)
        with connection.cursor() as cursor:
            if user.get("role")=="admin":
                cursor.execute(f'''SELECT `cdr`.`id`,
			`cdr`.`match_type`,
			`cdr`.`name_tournament`,
			`cdr`.`team1`,
			`cdr`.`team2`,
			`cdr`.`preparation_date`,
			`cdr`.`match_date`,
			`cdr`.`from_date`,
			`cdr`.`to_date`,
			`cdr`.`days_count`,
			`cdr`.`start_time`,
			`cdr`.`pitch_id`,
			`cdr`.`ground_id`,
			`cdr`.`is_pitch_level`,
			`cdr`.`lawn_height`,
			`cdr`.`grass_cover`,
			`cdr`.`min_temp`,
			`cdr`.`max_temp`,
			`cdr`.`forecast`,
			`cdr`.`moisture_upto`,
			`cdr`.`dew_factor`,
			`cdr`.`access_bounce`,
			`cdr`.`machinery_id`,
			`cdr`.`no_of_passes`,
			`cdr`.`rolling_speed`,
			`cdr`.`last_watering_on`,
			`cdr`.`quantity_of_water`,
			`cdr`.`time_of_application`,
			`cdr`.`time_roller`,
			`cdr`.`is_daily_watering`,
			`cdr`.`mover_machinery_id`,
			`cdr`.`date_mowing_done_last`,
			`cdr`.`time_of_application_mover`,
			`cdr`.`mowing_done_at_mm`,
			`cdr`.`is_fertilizers_used`,
			`cdr`.`fertilizers_details`,
			`cdr`.`chemical_details_remark`,
			`cdr`.`remark_by_groundsman`,
			`cdr`.`out_machinery_id`,
			`cdr`.`out_no_of_passes`,
			`cdr`.`out_rolling_speed`,
			`cdr`.`out_last_watering_on`,
			`cdr`.`out_quantity_of_water`,
			`cdr`.`out_time_of_application`,
			`cdr`.`out_time_roller`,
			`cdr`.`out_is_daily_watering`,
			`cdr`.`out_mover_machinery_id`,
			`cdr`.`out_date_mowing_done_last`,
			`cdr`.`time_of_application_out_mover`,
			`cdr`.`out_mowing_done_at_mm`,
			`cdr`.`out_is_fertilizers_used`,
			`cdr`.`out_fertilizers_details`,
			`cdr`.`out_chemical_details_remark`,
			`cdr`.`out_remark_by_groundsman`,
			`cdr`.`brief_match_pitch_assessment`,
			`cdr`.`time_of_application_chemical`,
			`cdr`.`out_time_of_application_chemical`,
			`cdr`.`created_at`,
			`cdr`.`updated_at`,
			`cdr`.`chemical_weight`,
			`cdr`.`fertilizers_unit`,
			`cdr`.`out_chemical_weight`,
			`cdr`.`out_fertilizers_unit`,
			`cdr`.`nuteral_curator`,
			`cdr`.`out_mover_machine_type`,
			`cdr`.`out_mover_machinery_name_operator`,
			`cdr`.`out_moving_passes_unit`,
			`cdr`.`out_mowing_duration`,
			`cdr`.`mover_machine_type`,
			`cdr`.`mover_machinery_name_operator`,
			`cdr`.`moving_passes_unit`,
			`cdr`.`mowing_duration`,
			`cdr`.`roller_machine_type`,
			`cdr`.`roller_machinery_name_operator`,
			`cdr`.`out_roller_machine_type`,
			`cdr`.`out_roller_machinery_name_operator`,
			`cdr`.`passes_unit`,
			`cdr`.`out_passes_unit`,
			g.ground_name,
			p.pitch_type, 
			p.pitch_placement, 
			c1.chemical_name as chem1,
			c2.chemical_name as chem2,
			m1.print_details as mch1,
			m2.print_details as mch2,
			m3.print_details as mch3,
			m4.print_details as mch4,
   `cdr`.`rolling_date`,
   `cdr`.`out_rolling_date`
   


			  

		FROM 
								{org_id}_match_master cdr
							INNER JOIN 
								{org_id}_pitch_master p ON cdr.pitch_id = p.id
							INNER JOIN 
								{org_id}_ground_master g ON cdr.ground_id = g.id
							LEFT JOIN 
								{org_id}_machinery_master m1 ON cdr.machinery_id = m1.id
							LEFT JOIN 
								{org_id}_machinery_master m2 ON cdr.mover_machinery_id = m2.id
							LEFT JOIN 
								{org_id}_machinery_master m3 ON cdr.out_machinery_id = m3.id
							LEFT JOIN 
								{org_id}_machinery_master m4 ON cdr.out_mover_machinery_id = m4.id
							LEFT JOIN 
								`{org_id}_fertilizer_master` c1 ON cdr.fertilizers_details = c1.id
							LEFT JOIN 
								`{org_id}_fertilizer_master` c2 ON cdr.out_fertilizers_details = c2.id
						   
							order by cdr.created_at desc''')
            else:
                cursor.execute(f'''SELECT `cdr`.`id`,
			`cdr`.`match_type`,
			`cdr`.`name_tournament`,
			`cdr`.`team1`,
			`cdr`.`team2`,
			`cdr`.`preparation_date`,
			`cdr`.`match_date`,
			`cdr`.`from_date`,
			`cdr`.`to_date`,
			`cdr`.`days_count`,
			`cdr`.`start_time`,
			`cdr`.`pitch_id`,
			`cdr`.`ground_id`,
			`cdr`.`is_pitch_level`,
			`cdr`.`lawn_height`,
			`cdr`.`grass_cover`,
			`cdr`.`min_temp`,
			`cdr`.`max_temp`,
			`cdr`.`forecast`,
			`cdr`.`moisture_upto`,
			`cdr`.`dew_factor`,
			`cdr`.`access_bounce`,
			`cdr`.`machinery_id`,
			`cdr`.`no_of_passes`,
			`cdr`.`rolling_speed`,
			`cdr`.`last_watering_on`,
			`cdr`.`quantity_of_water`,
			`cdr`.`time_of_application`,
			`cdr`.`time_roller`,
			`cdr`.`is_daily_watering`,
			`cdr`.`mover_machinery_id`,
			`cdr`.`date_mowing_done_last`,
			`cdr`.`time_of_application_mover`,
			`cdr`.`mowing_done_at_mm`,
			`cdr`.`is_fertilizers_used`,
			`cdr`.`fertilizers_details`,
			`cdr`.`chemical_details_remark`,
			`cdr`.`remark_by_groundsman`,
			`cdr`.`out_machinery_id`,
			`cdr`.`out_no_of_passes`,
			`cdr`.`out_rolling_speed`,
			`cdr`.`out_last_watering_on`,
			`cdr`.`out_quantity_of_water`,
			`cdr`.`out_time_of_application`,
			`cdr`.`out_time_roller`,
			`cdr`.`out_is_daily_watering`,
			`cdr`.`out_mover_machinery_id`,
			`cdr`.`out_date_mowing_done_last`,
			`cdr`.`time_of_application_out_mover`,
			`cdr`.`out_mowing_done_at_mm`,
			`cdr`.`out_is_fertilizers_used`,
			`cdr`.`out_fertilizers_details`,
			`cdr`.`out_chemical_details_remark`,
			`cdr`.`out_remark_by_groundsman`,
			`cdr`.`brief_match_pitch_assessment`,
			`cdr`.`time_of_application_chemical`,
			`cdr`.`out_time_of_application_chemical`,
			`cdr`.`created_at`,
			`cdr`.`updated_at`,
			`cdr`.`chemical_weight`,
			`cdr`.`fertilizers_unit`,
			`cdr`.`out_chemical_weight`,
			`cdr`.`out_fertilizers_unit`,
			`cdr`.`nuteral_curator`,
			`cdr`.`out_mover_machine_type`,
			`cdr`.`out_mover_machinery_name_operator`,
			`cdr`.`out_moving_passes_unit`,
			`cdr`.`out_mowing_duration`,
			`cdr`.`mover_machine_type`,
			`cdr`.`mover_machinery_name_operator`,
			`cdr`.`moving_passes_unit`,
			`cdr`.`mowing_duration`,
			`cdr`.`roller_machine_type`,
			`cdr`.`roller_machinery_name_operator`,
			`cdr`.`out_roller_machine_type`,
			`cdr`.`out_roller_machinery_name_operator`,
			`cdr`.`passes_unit`,
			`cdr`.`out_passes_unit`,
			g.ground_name,
			p.pitch_type, 
			p.pitch_placement, 
			c1.chemical_name as chem1,
			c2.chemical_name as chem2,
			m1.print_details as mch1,
			m2.print_details as mch2,
			m3.print_details as mch3,
			m4.print_details as mch4,
   `cdr`.`rolling_date`,
   `cdr`.`out_rolling_date`

		FROM {org_id}_match_master cdr
							INNER JOIN 
								{org_id}_pitch_master p ON cdr.pitch_id = p.id
							INNER JOIN 
								{org_id}_ground_master g ON cdr.ground_id = g.id
							LEFT JOIN 
								{org_id}_machinery_master m1 ON cdr.machinery_id = m1.id
							LEFT JOIN 
								{org_id}_machinery_master m2 ON cdr.mover_machinery_id = m2.id
							LEFT JOIN 
								{org_id}_machinery_master m3 ON cdr.out_machinery_id = m3.id
							LEFT JOIN 
								{org_id}_machinery_master m4 ON cdr.out_mover_machinery_id = m4.id
							LEFT JOIN 
								`{org_id}_fertilizer_master` c1 ON cdr.fertilizers_details = c1.id
							LEFT JOIN 
								`{org_id}_fertilizer_master` c2 ON cdr.out_fertilizers_details = c2.id
						   
							 where cdr.ground_id=%s order by `created_at` desc''',[user.get("ground_id")])
                
            matches = cursor.fetchall()


        return render(request, 'admin_user/match_list.html', {'matches': matches})
    except Exception as e:
        print(e)


from django.http import JsonResponse
from django.db import connection


# # View to get all Ground IDs
# def get_grounds(request):
#     with connection.cursor() as cursor:
#         cursor.execute("SELECT id FROM yourapp_ground")
#         rows = cursor.fetchall()
#
#     # Convert the result into a list of dictionaries
#     ground_list = [{'id': row[0]} for row in rows]
#     return JsonResponse(ground_list, safe=False)
#
#
# # View to get Pitches based on selected Ground ID
# def get_pitches(request, ground_id):
#     with connection.cursor() as cursor:
#         cursor.execute("SELECT id FROM yourapp_pitch WHERE ground_id = %s", [ground_id])
#         rows = cursor.fetchall()
#
#     # Convert the result into a list of dictionaries
#     pitch_list = [{'id': row[0]} for row in rows]
#     return JsonResponse(pitch_list, safe=False)

##################### Backup data #####################

import pandas as pd
from django.db import connection
from django.http import HttpResponse
from io import BytesIO
import zipfile

def export_multiple_tables_to_excel(request):
    try:
        org_id = request.session["org_id"]
        data = json.loads(request.body)
        filter_date = data.get("date", None)
        if not filter_date:
                return JsonResponse({"error": "Date is required"}, status=400)
        queries = {
            'Table1': f"SELECT * FROM {org_id}_curator_daily_recording_master WHERE created_at <= '{filter_date}'",
            'Table2': f"SELECT * FROM {org_id}_fertilizer_master",
            'Table3': f"SELECT * FROM {org_id}_match_master WHERE created_at <= '{filter_date}'",
            'Table4': f"SELECT * FROM {org_id}_match_scores_master WHERE created_at <= '{filter_date}'",
            'Table5': f"SELECT * FROM {org_id}_pitch_master",
            'Table6': f"SELECT * FROM {org_id}_ground_master",
            'Table7': f"SELECT * FROM {org_id}_machinery_master",
        }

        print("Queries to be executed:", queries)
        # In-memory zip buffer
        zip_buffer = BytesIO()
        
        with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED) as zip_file:
            for table_name, query in queries.items():
                with connection.cursor() as cursor:
                    cursor.execute(query)
                    columns = [col[0] for col in cursor.description]
                    data = cursor.fetchall()

                # Excel file for each table
                df = pd.DataFrame(data, columns=columns)
                excel_buffer = BytesIO()
                with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name=table_name)
                excel_buffer.seek(0)
                zip_file.writestr(f"{table_name}.xlsx", excel_buffer.read())

                # SQL insert statements for each table
                sql_content = ""
                for row in data:
                    values = []
                    for val in row:
                        if val is None:
                            values.append('NULL')
                        elif isinstance(val, str):
                            values.append("'" + val.replace("'", "''") + "'")
                        else:
                            values.append(str(val))
                    insert_stmt = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({', '.join(values)});\n"
                    sql_content += insert_stmt
                zip_file.writestr(f"{table_name}.sql", sql_content)
        
        zip_buffer.seek(0)
        insert_export_log(filter_date, "SQL-Excel Export",org_id)
        response = HttpResponse(zip_buffer, content_type='application/zip')
        response['Content-Disposition'] = 'attachment; filename=multiple_tables_export.zip'
        return response
    except Exception as e:
        print("Error during export:", e)
        return JsonResponse({"error": str(e)}, status=500)





from django.db import connection
from django.http import HttpResponse
from io import BytesIO
import zipfile

def export_multiple_sql_files_in_zip(request):
    try:
        org_id = request.session["org_id"]
        data = json.loads(request.body)
        filter_date = data.get("date", None)
        if not filter_date:
                return JsonResponse({"error": "Date is required"}, status=400)
        queries = {
            'Table1': f"SELECT * FROM {org_id}_curator_daily_recording_master WHERE created_at <= '{filter_date}'",
            'Table2': f"SELECT * FROM {org_id}_fertilizer_master",
            'Table3': f"SELECT * FROM {org_id}_match_master WHERE created_at <= '{filter_date}'",
            'Table4': f"SELECT * FROM {org_id}_match_scores_master WHERE created_at <= '{filter_date}'",
            'Table5': f"SELECT * FROM {org_id}_pitch_master",
            'Table6': f"SELECT * FROM {org_id}_ground_master",
            'Table7': f"SELECT * FROM {org_id}_machinery_master",
        }

        zip_buffer = BytesIO()

        with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED) as zip_file:
            for table_name, query in queries.items():
                with connection.cursor() as cursor:
                    cursor.execute(query)
                    columns = [col[0] for col in cursor.description]
                    rows = cursor.fetchall()

                sql_content = ""
                for row in rows:
                    values = []
                    for val in row:
                        if val is None:
                            values.append('NULL')
                        elif isinstance(val, str):
                            # Escape single quotes for SQL strings
                            values.append("'" + val.replace("'", "''") + "'")
                        else:
                            values.append(str(val))
                    insert_stmt = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({', '.join(values)});\n"
                    sql_content += insert_stmt

                zip_file.writestr(f"{table_name}.sql", sql_content)

        zip_buffer.seek(0)
        insert_export_log(filter_date, "SQL Export",org_id)
        response = HttpResponse(zip_buffer, content_type='application/zip')
        response['Content-Disposition'] = 'attachment; filename=multiple_sql_export.zip'

        return response
    except Exception as e:
        print("Error during export:", e)
        return JsonResponse({"error": str(e)}, status=500)


def export_form(request):
    # Render the export form template
    return render(request, 'admin_user/backup/backup_form.html')

from django.db import connection

def insert_export_log(export_date, export_type,org_id):
    try:
        with connection.cursor() as cursor:
            query = f"""
            INSERT INTO {org_id}_export_logs_master (export_date, export_type, created_at, updated_at)
            VALUES (%s, %s, NOW(), NOW())
            """
            cursor.execute(query, [export_date, export_type])
    except Exception as e:
        print("Error inserting export log:", e) 


def get_export_logs(request):
    try:
        # SQL: DESCENDING order by created_at
        org_id = request.session["org_id"]
        query = f"""
            SELECT id, export_date, export_type, created_at, updated_at
            FROM {org_id}_export_logs_master
            ORDER BY created_at DESC
        """
        with connection.cursor() as cursor:
            cursor.execute(query)
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()

        # JSON: list of dicts
        logs = [dict(zip(columns, row)) for row in rows]
        return JsonResponse({'logs': logs})
    except Exception as e:
        print("Error fetching export logs:", e)
        return JsonResponse({"error": str(e)}, status=500)

##################### Backup data #####################