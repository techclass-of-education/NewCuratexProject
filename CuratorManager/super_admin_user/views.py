from .models import SuperAdmin, AdminUserList
from django.shortcuts import render, redirect
from .templates.super_admin_user.admin.adminForm import AdminUserForm
from django.contrib import messages
from django.db import connection
from .models import MastersList
from admin_user.forms.adminRoleForm import AdminUserRoleForm
from .templates.super_admin_user.admin.adminUpdate import AdminUserUpdateForm
from django.shortcuts import render, get_object_or_404, redirect


def login(request):
    return render(request, 'admin_user/org_login.html')


def login_auth(request):
    print("lofin")
    try:
        if request.method == 'POST':
            username = request.POST['username']
            password = request.POST['password']
            # SuperAdmin.objects.
            try:
                user = SuperAdmin.objects.get( username=username, password=password)
                if user is not None:
                    # print(user.name)
                   
                    request.session["superuser"] = {
                    "id": user.id,
                    "name": user.name,
                   
                    "email": user.email,
                    "username": user.username,
                    "address":user.address,
                    "mobile":user.mobile,
                    
                    }
                    return render(request, 'super_admin_user/dashboard.html',{'user':user})
                else:
                    messages.error(request, 'Invalid username or password')
                    return render(request, 'super_admin_user/login.html')
            except Exception as e:
                print(e)
                return render(request, 'super_admin_user/login.html')
    except Exception as e:
         print(e)


def dashboard(request):
    return render(request, 'super_admin_user/dashboard.html')


def logout_root(request):
    return redirect('login_root')


# views.py

def createTable(tableName,t,org):
    try:
     with connection.cursor() as cursor:
        if(t=="state"):
            sql=f'''SET FOREIGN_KEY_CHECKS=0;
            CREATE TABLE IF NOT EXISTS {tableName} (
        id INT AUTO_INCREMENT PRIMARY KEY,
        state VARCHAR(255) NOT NULL UNIQUE,
        state_code VARCHAR(2) NOT NULL UNIQUE,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        );SET FOREIGN_KEY_CHECKS=1;
        '''
            cursor.execute(sql)
        elif (t == "city"):
            sql = f'''SET FOREIGN_KEY_CHECKS=0;
            CREATE TABLE IF NOT EXISTS {tableName} (
                id INT AUTO_INCREMENT PRIMARY KEY,
                city_name VARCHAR(255) NOT NULL UNIQUE,
                state_id INT DEFAULT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            );SET FOREIGN_KEY_CHECKS=1;
            '''
            cursor.execute(sql)
        elif (t == "fertilizer"):
            sql = f'''SET FOREIGN_KEY_CHECKS=0;
            CREATE TABLE IF NOT EXISTS {tableName} (
                `id` int NOT NULL AUTO_INCREMENT,
                `chemical_name` text NOT NULL,
                `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
                `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                `chemical_type` varchar(45) NOT NULL,
                PRIMARY KEY (`id`)
            );SET FOREIGN_KEY_CHECKS=1;
            '''
            cursor.execute(sql)

        elif (t == "ground"):
            sql = f'''SET FOREIGN_KEY_CHECKS=0;
            CREATE TABLE IF NOT EXISTS {tableName} (
             `id` int NOT NULL AUTO_INCREMENT,
  `org_id` varchar(255) DEFAULT NULL,
  `google_location` text,
  `year_of_construction` varchar(255) DEFAULT NULL,
  `phone_numbers` varchar(255) DEFAULT NULL,
  `slop_ratio` varchar(255) DEFAULT NULL,
  `ground_name` varchar(255) DEFAULT NULL,
  `state_code` varchar(2) DEFAULT NULL,
  `state_name` varchar(255) DEFAULT NULL,
  `city_name` varchar(255) DEFAULT NULL,
  `count_main_pitches` int DEFAULT NULL,
  `count_practice_pitches` int DEFAULT NULL,
  `is_side_screen` tinyint(1) DEFAULT NULL,
  `count_placement_side_screen` int DEFAULT NULL,
  `is_broadcasting_facility` tinyint(1) DEFAULT NULL,
  `is_irrigation_pitches` tinyint(1) DEFAULT NULL,
  `count_hydrants` int DEFAULT NULL,
  `count_pumps` int DEFAULT NULL,
  `count_showers` int DEFAULT NULL,
  `is_lawn_nursary` tinyint(1) DEFAULT NULL,
  `name_centre_square` varchar(255) DEFAULT NULL,
  `is_curator_room` tinyint(1) DEFAULT NULL,
  `is_seperate_practice_area` tinyint(1) DEFAULT NULL,
  `outfield` varchar(255) DEFAULT NULL,
  `profile_of_outfield` varchar(255) DEFAULT NULL,
  `lawn_species` varchar(255) DEFAULT NULL,
  `is_drainage_system_available` tinyint(1) DEFAULT NULL,
  `is_water_drainage_system` tinyint(1) DEFAULT NULL,
  `is_irrigation_system_available` tinyint(1) DEFAULT NULL,
  `is_availability_of_water` tinyint(1) DEFAULT NULL,
  `water_source` text,
  `storage_capacity_in_litres` int DEFAULT NULL,
  `count_pop_ups` int DEFAULT NULL,
  `size_of_pumps` varchar(255) DEFAULT NULL,
  `is_automation_if_any` tinyint(1) DEFAULT NULL,
  `is_ground_equipments` tinyint(1) DEFAULT NULL,
  `is_maintenance_contract` tinyint(1) DEFAULT NULL,
  `is_maintenance_agency` tinyint(1) DEFAULT NULL,
  `boundary_size_mtrs` text,
  `is_availability_of_mot` tinyint(1) DEFAULT NULL,
  `is_machine_shed` tinyint(1) DEFAULT NULL,
  `is_soil_shed` tinyint(1) DEFAULT NULL,
  `is_pitch_or_run_up_covers` tinyint(1) DEFAULT NULL,
  `size_of_covers_in_mtrs` varchar(255) DEFAULT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `screen_size` varchar(255) DEFAULT NULL,
  `broadcast_video_analysis` varchar(255) DEFAULT NULL,
  `outfield_type` varchar(255) DEFAULT NULL,
  `lawn_species_out` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`)
        );SET FOREIGN_KEY_CHECKS=1;
            '''
            cursor.execute(sql)
        elif (t == "pitch"):
            sql = f'''SET FOREIGN_KEY_CHECKS=0;
            CREATE TABLE IF NOT EXISTS {tableName} (
           `id` int NOT NULL AUTO_INCREMENT,
  `org_id` varchar(255) DEFAULT NULL,
  `ground_id` int DEFAULT NULL,
  `size_pitch_square` text,
  `pitch_no` varchar(255) DEFAULT NULL,
  `pitch_type` varchar(255) DEFAULT NULL,
  `profile_of_pitches` varchar(255) DEFAULT NULL,
  `last_used_date` date DEFAULT NULL,
  `last_used_match` varchar(255) DEFAULT NULL,
  `soil_type` varchar(255) DEFAULT NULL,
  `is_uniformtiy_of_grass` tinyint(1) DEFAULT NULL,
  `size_of_grass` text,
  `mowing_last_date` date DEFAULT NULL,
  `size_pitch` varchar(45) DEFAULT NULL,
  `pitch_placement` varchar(45) DEFAULT NULL,
  `pitch_in_out` varchar(45) DEFAULT NULL,
  `mowing_size` text,
  `start_date_of_pitch_preparation` date DEFAULT NULL,
  `date_pitch_construction` date DEFAULT NULL,
  `pitch_details` text,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
        );SET FOREIGN_KEY_CHECKS=1;
            '''
            cursor.execute(sql)
            
        elif (t == "curator_daily_recording"):
            cursor.execute(f'''SET FOREIGN_KEY_CHECKS=0;

CREATE TABLE IF NOT EXISTS {tableName} (
    `id` int NOT NULL AUTO_INCREMENT,
  `pitch_id` int DEFAULT '0',
  `pitch_location` varchar(100) DEFAULT NULL,
  `rolling_start_date` varchar(50) DEFAULT NULL,
  `min_temp` varchar(45) DEFAULT NULL,
  `max_temp` varchar(45) DEFAULT NULL,
  `forecast` text,
  `clagg_hammer` text,
  `moisture` text,
  `machinery_id` varchar(100) DEFAULT NULL,
  `no_of_passes` varchar(50) DEFAULT NULL,
  `rolling_speed` varchar(50) DEFAULT NULL,
  `last_watering_on` varchar(50) DEFAULT NULL,
  `quantity_of_water` varchar(50) DEFAULT NULL,
  `time_of_application` varchar(20) DEFAULT NULL,
  `time_roller` varchar(20) DEFAULT NULL,
  `mover_machinery_id` varchar(100) DEFAULT NULL,
  `date_mowing_done_last` varchar(50) DEFAULT NULL,
  `time_of_application_mover` varchar(20) DEFAULT NULL,
  `mowing_done_at_mm` varchar(50) DEFAULT NULL,
  `is_fertilizers_used` varchar(20) DEFAULT NULL,
  `fertilizers_details` text,
  `chemical_details_remark` longtext,
  `remark_by_groundsman` text,
  `out_machinery_id` varchar(100) DEFAULT NULL,
  `out_no_of_passes` varchar(50) DEFAULT NULL,
  `out_rolling_speed` varchar(50) DEFAULT NULL,
  `out_last_watering_on` varchar(50) DEFAULT NULL,
  `out_quantity_of_water` varchar(50) DEFAULT NULL,
  `out_time_of_application` varchar(20) DEFAULT NULL,
  `out_time_roller` varchar(20) DEFAULT NULL,
  `out_mover_machinery_id` varchar(100) DEFAULT NULL,
  `out_date_mowing_done_last` varchar(50) DEFAULT NULL,
  `time_of_application_out_mover` varchar(20) DEFAULT NULL,
  `out_mowing_done_at_mm` varchar(50) DEFAULT NULL,
  `out_is_fertilizers_used` varchar(20) DEFAULT NULL,
  `out_fertilizers_details` text,
  `out_chemical_details_remark` longtext,
  `out_remark_by_groundsman` text,
  `practice_machinery_id` varchar(100) DEFAULT NULL,
  `practice_no_of_passes` varchar(50) DEFAULT NULL,
  `practice_rolling_speed` varchar(50) DEFAULT NULL,
  `practice_last_watering_on` varchar(50) DEFAULT NULL,
  `practice_quantity_of_water` varchar(50) DEFAULT NULL,
  `practice_time_of_application` varchar(20) DEFAULT NULL,
  `practice_time_roller` varchar(20) DEFAULT NULL,
  `practice_mover_machinery_id` varchar(100) DEFAULT NULL,
  `practice_date_mowing_done_last` varchar(50) DEFAULT NULL,
  `time_of_application_practice_mover` varchar(20) DEFAULT NULL,
  `practice_mowing_done_at_mm` varchar(50) DEFAULT NULL,
  `practice_is_fertilizers_used` varchar(20) DEFAULT NULL,
  `practice_fertilizers_details` text,
  `practice_chemical_details_remark` longtext,
  `practice_remark_by_groundsman` text,
  `time_of_application_chemical` varchar(20) DEFAULT NULL,
  `out_time_of_application_chemical` varchar(20) DEFAULT NULL,
  `practice_time_of_application_chemical` varchar(20) DEFAULT NULL,
  `recording_type` varchar(45) DEFAULT NULL,
  `ground_id` int DEFAULT '0',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `pitch_main` varchar(20) NOT NULL,
  `pitch_practice` varchar(20) NOT NULL,
  `outfield` varchar(20) NOT NULL,
  `practice_area` varchar(20) NOT NULL,
  `pp_machinery_id` varchar(100) DEFAULT NULL,
  `pp_no_of_passes` varchar(50) DEFAULT NULL,
  `pp_rolling_speed` varchar(50) DEFAULT NULL,
  `pp_last_watering_on` varchar(50) DEFAULT NULL,
  `pp_quantity_of_water` varchar(50) DEFAULT NULL,
  `pp_time_of_application` varchar(20) DEFAULT NULL,
  `pp_time_roller` varchar(20) DEFAULT NULL,
  `pp_mover_machinery_id` varchar(100) DEFAULT NULL,
  `pp_date_mowing_done_last` varchar(50) DEFAULT NULL,
  `pp_time_of_application_mover` varchar(20) DEFAULT NULL,
  `pp_mowing_done_at_mm` varchar(50) DEFAULT NULL,
  `pp_is_fertilizers_used` varchar(20) DEFAULT NULL,
  `pp_fertilizers_details` text,
  `pp_chemical_details_remark` longtext,
  `pp_remark_by_groundsman` text,
  `pp_time_of_application_chemical` varchar(20) DEFAULT NULL,
  `pitch_main_chemical_weight` varchar(20) DEFAULT NULL,
  `pitch_practice_chemical_weight` varchar(20) DEFAULT NULL,
  `outfield_chemical_weight` varchar(20) DEFAULT NULL,
  `practice_area_chemical_weight` varchar(20) DEFAULT NULL,
  `pitch_main_chemical_unit` varchar(20) DEFAULT NULL,
  `pitch_practice_chemical_unit` varchar(20) DEFAULT NULL,
  `outfield_chemical_unit` varchar(20) DEFAULT NULL,
  `practice_area_chemical_unit` varchar(20) DEFAULT NULL,
  `pp_mover_machine_type` varchar(100) DEFAULT NULL,
  `pp_mover_machinery_name_operator` varchar(100) DEFAULT NULL,
  `pp_moving_passes_unit` varchar(255) DEFAULT NULL,
  `pp_mowing_duration` varchar(100) DEFAULT NULL,
  `practice_mover_machine_type` varchar(100) DEFAULT NULL,
  `practice_mover_machinery_name_operator` varchar(100) DEFAULT NULL,
  `practice_moving_passes_unit` varchar(255) DEFAULT NULL,
  `practice_mowing_duration` varchar(100) DEFAULT NULL,
  `out_mover_machine_type` varchar(100) DEFAULT NULL,
  `out_mover_machinery_name_operator` varchar(100) DEFAULT NULL,
  `out_moving_passes_unit` varchar(255) DEFAULT NULL,
  `out_mowing_duration` varchar(100) DEFAULT NULL,
  `mover_machine_type` varchar(100) DEFAULT NULL,
  `mover_machinery_name_operator` varchar(100) DEFAULT NULL,
  `moving_passes_unit` varchar(255) DEFAULT NULL,
  `mowing_duration` varchar(100) DEFAULT NULL,
  `roller_machine_type` varchar(100) DEFAULT NULL,
  `roller_machinery_name_operator` varchar(255) DEFAULT NULL,
  `pp_roller_machine_type` varchar(100) DEFAULT NULL,
  `pp_roller_machinery_name_operator` varchar(255) DEFAULT NULL,
  `out_roller_machine_type` varchar(100) DEFAULT NULL,
  `out_roller_machinery_name_operator` varchar(255) DEFAULT NULL,
  `practice_roller_machine_type` varchar(100) DEFAULT NULL,
  `practice_roller_machinery_name_operator` varchar(255) DEFAULT NULL,
  `passes_unit` varchar(255) DEFAULT NULL,
  `out_passes_unit` varchar(255) DEFAULT NULL,
  `pp_passes_unit` varchar(255) DEFAULT NULL,
  `practice_passes_unit` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`)
);

SET FOREIGN_KEY_CHECKS=1;
''')
            
            # sql = 
            # print(sql)
            # try:
            #     cursor.execute(sql)
            #     print("huaaaa")
            # except Exception as e:
            #     print(e)
        elif (t == "machinery"):
            sql = f'''SET FOREIGN_KEY_CHECKS=0;
        CREATE TABLE IF NOT EXISTS {tableName} (    
      `id` int NOT NULL AUTO_INCREMENT,
            `equipment_name` varchar(255) DEFAULT NULL,
            `type` varchar(255) NOT NULL,
            `date_purchase` varchar(30) DEFAULT NULL,
            `unit` varchar(50) DEFAULT NULL,
            `value` text,
            `model` varchar(45) DEFAULT NULL,
            `print_details` varchar(255) DEFAULT NULL,
      PRIMARY KEY (`id`)
            );SET FOREIGN_KEY_CHECKS=1;'''
            cursor.execute(sql)
        elif (t == "match_scores"):
            sql = f'''SET FOREIGN_KEY_CHECKS=0;
            CREATE TABLE IF NOT EXISTS {tableName} (    
             `id` int NOT NULL AUTO_INCREMENT,
  `match_id` int DEFAULT NULL,
  `day` int DEFAULT '1',
  `team` text,
  `inning` int DEFAULT NULL,
  `session` int DEFAULT NULL,
  `wickets` int DEFAULT NULL,
  `overs` float DEFAULT NULL,
  `runs` int DEFAULT NULL,
  `winner` int DEFAULT NULL,
  `day_end` varchar(45) DEFAULT NULL,
  `remark` mediumtext,
  `wonby` text,
  `elected` text,
  PRIMARY KEY (`id`)


        );SET FOREIGN_KEY_CHECKS=1;
                            '''
            cursor.execute(sql)
        elif (t == "export_log"):
            sql = f'''SET FOREIGN_KEY_CHECKS=0;
            CREATE TABLE IF NOT EXISTS {tableName} (    
            id INT AUTO_INCREMENT PRIMARY KEY,
    export_date DATE NOT NULL,               
    export_type VARCHAR(20) NOT NULL,      
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        );SET FOREIGN_KEY_CHECKS=1;'''
            cursor.execute(sql)

        elif (t == "match"):
            sql = f'''SET FOREIGN_KEY_CHECKS=0;
          CREATE TABLE IF NOT EXISTS {tableName} (
            `id` int NOT NULL AUTO_INCREMENT,
  `match_type` varchar(700) DEFAULT NULL,
  `name_tournament` varchar(700) DEFAULT NULL,
  `team1` varchar(700) DEFAULT NULL,
  `team2` varchar(700) DEFAULT NULL,
  `preparation_date` text,
  `match_date` text,
  `from_date` text,
  `to_date` text,
  `days_count` text,
  `start_time` text,
  `pitch_id` int DEFAULT NULL,
  `ground_id` int DEFAULT NULL,
  `is_pitch_level` text,
  `lawn_height` text,
  `grass_cover` varchar(700) DEFAULT NULL,
  `min_temp` text,
  `max_temp` text,
  `forecast` text,
  `moisture_upto` text,
  `dew_factor` text,
  `access_bounce` text,
  `machinery_id` text,
  `no_of_passes` text,
  `rolling_speed` text,
  `last_watering_on` text,
  `quantity_of_water` text,
  `time_of_application` text,
  `time_roller` text,
  `is_daily_watering` text,
  `mover_machinery_id` text,
  `date_mowing_done_last` text,
  `time_of_application_mover` text,
  `mowing_done_at_mm` text,
  `is_fertilizers_used` text,
  `fertilizers_details` varchar(700) DEFAULT NULL,
  `chemical_details_remark` longtext,
  `remark_by_groundsman` varchar(700) DEFAULT NULL,
  `out_machinery_id` text,
  `out_no_of_passes` text,
  `out_rolling_speed` text,
  `out_last_watering_on` text,
  `out_quantity_of_water` text,
  `out_time_of_application` text,
  `out_time_roller` text,
  `out_is_daily_watering` text,
  `out_mover_machinery_id` text,
  `out_date_mowing_done_last` text,
  `time_of_application_out_mover` text,
  `out_mowing_done_at_mm` text,
  `out_is_fertilizers_used` text,
  `out_fertilizers_details` varchar(700) DEFAULT NULL,
  `out_chemical_details_remark` longtext,
  `out_remark_by_groundsman` varchar(700) DEFAULT NULL,
  `brief_match_pitch_assessment` text,
  `time_of_application_chemical` varchar(700) DEFAULT NULL,
  `out_time_of_application_chemical` varchar(700) DEFAULT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `chemical_weight` varchar(700) DEFAULT NULL,
  `fertilizers_unit` varchar(700) DEFAULT NULL,
  `out_chemical_weight` varchar(700) DEFAULT NULL,
  `out_fertilizers_unit` varchar(700) DEFAULT NULL,
  `nuteral_curator` varchar(700) DEFAULT NULL,
  `out_mover_machine_type` varchar(700) DEFAULT NULL,
  `out_mover_machinery_name_operator` varchar(700) DEFAULT NULL,
  `out_moving_passes_unit` varchar(700) DEFAULT NULL,
  `out_mowing_duration` varchar(700) DEFAULT NULL,
  `mover_machine_type` varchar(700) DEFAULT NULL,
  `mover_machinery_name_operator` varchar(700) DEFAULT NULL,
  `moving_passes_unit` varchar(700) DEFAULT NULL,
  `mowing_duration` varchar(700) DEFAULT NULL,
  `roller_machine_type` varchar(700) DEFAULT NULL,
  `roller_machinery_name_operator` varchar(700) DEFAULT NULL,
  `out_roller_machine_type` varchar(700) DEFAULT NULL,
  `out_roller_machinery_name_operator` varchar(700) DEFAULT NULL,
  `passes_unit` varchar(700) DEFAULT NULL,
  `out_passes_unit` varchar(700) DEFAULT NULL,
  `rolling_date` varchar(700) DEFAULT NULL,
  `out_rolling_date` varchar(700) DEFAULT NULL,
  PRIMARY KEY (`id`)); SET FOREIGN_KEY_CHECKS=1;'''
            cursor.execute(sql)
        
        elif (t=="icc_pitch_report"):
            sql=f'''SET FOREIGN_KEY_CHECKS=0;
          CREATE TABLE IF NOT EXISTS {tableName} (
  `id` int NOT NULL AUTO_INCREMENT,
  `match_id` int NOT NULL,
  `ground_id` int NOT NULL,
  `referee` varchar(150) DEFAULT NULL,
  `grass_uniform` varchar(5) DEFAULT NULL,
  `grass_cover` varchar(20) DEFAULT NULL,
  `grass_details` text,
  `pitch_dry` varchar(5) DEFAULT NULL,
  `pitch_dry_details` text,
  `pitch_comment` text,
  `heavy_roller_days` varchar(50) DEFAULT NULL,
  `heavy_roller_effect` json DEFAULT NULL,
  `bounce` json DEFAULT NULL,
  `bounce_consistency` json DEFAULT NULL,
  `seam_movement` json DEFAULT NULL,
  `turn` json DEFAULT NULL,
  `pitch_rating` varchar(20) DEFAULT NULL,
  `outfield_rating` varchar(20) DEFAULT NULL,
  `final_comment` text,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
);SET FOREIGN_KEY_CHECKS=1;

            '''
            cursor.execute(sql)
   
    except Exception as e:
         print(e.message)
    addMachinery(org)
    addChemicals(org)

def addMachinery(org):
    try:
        with connection.cursor() as cursor:
            # Define the table name safely
            table_name = f"{org}_machinery_master"
            
            # Updated INSERT query to include "print_details"
            sql = f"""
                INSERT INTO `{table_name}` 
                (`id`,`equipment_name`,`type`,`date_purchase`,`unit`,`value`,`model`,`print_details`) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            # Updated data with 8 values per record
            data = [
               (1,'Roller','Manual','2025-08-27','kg','500.00','local','Manual 500 kg'),
(2,'Roller','Manual','2025-08-27','kg','750.00','local','Manual 750 kg'),
(3,'Roller','Manual','2025-08-27','kg','1000.00','local','Manual 1000 kg'),
(4,'Roller','Manual','2025-08-27','kg','1500.00','local','Manual 1500 kg'),
(5,'Roller','Mechanised','2025-08-27','kg','500.00','single drum perol','Mechanised 500 kg'),
(6,'Roller','Mechanised','2025-08-27','kg','1000.00','single drum perol','Mechanised 1000 kg'),
(7,'Roller','Mechanised','2025-08-27','kg','1000.00','tandom','Mechanised 1000 kg'),
(8,'Roller','Mechanised','2025-08-27','kg','2000.00','tandom','Mechanised 2000 kg'),
(9,'Roller','Mechanised','2025-08-27','kg','2200.00','tandom','Mechanised 2200 kg'),
(10,'SuperSopper','Mechanised','2025-08-27','inches','72','aqua','Mechanised 72 inches'),
(11,'SuperSopper','Mechanised','2025-08-27','inches','48','aqua','Mechanised 36 inches'),
(12,'Aerator Procore 648','Mechanised','2025-08-27','NA','N/A','petrol','Mini Petrol'),
(13,'Scarifier Graden','Mechanised','2025-08-27','NA','N/A','petrol','GRADEN'),
(14,'Lawn Mower Outfield','Mechanised','2025-08-27','NA','N/A','petrol black','Tractor Petrol black'),
(15,'Lawn Mower Outfield','Mechanised','2025-08-27','NA','N/A','petrol yellow','Tractor Petrol yellow'),
(16,'Lawn Mower Outfield','Mechanised','2025-08-27','NA','N/A','TORO 3250','Toro 3250 - 1'),
(17,'Lawn Mower Pitch','Mechanised','2025-08-27','NA','0.00','toro 1000','Mechanised Toro 1000'),
(18,'Top Dresser','Mechanised','2025-08-27','NA','0.00','toro','Mechanised Toro'),
(19,'Kiss Cutter','Mechanised','2025-08-27','NA','0.00','turfco','Mechanised Turfco'),
(20,'Bush Cutter','Mechanised','2025-08-27','NA','0.00','styhl','Mechanised Styhl'),
(21,'Lawn Mower Outfield','Mechanised','2025-08-27','NA','N/A','STIHL','Bush Cutter'),
(22,'Spray Pump','Mechanised','2025-08-27','liter','15','STIHL','STIHL 15 L Sprayer'),
(23,'Spreader','Mechanised','2025-08-27','NA','2.00','local','Manual Spreader'),
(24,'Back lapping Machine','Mechanised','2025-08-27','NA','1.00','local','Back Lapping'),
(25,'Trolley','Manual','2025-08-27','NA','0.00','local','Trolley'),
(26,'Pitch Covers','Mechanised','2025-08-27','NA','120x100','local','120x100'),
(27,'Pitch Covers','Manual','2025-08-27','NA','110x100','local','110x100'),
(28,'Pitch Covers','Manual','2025-08-27','NA','100x100','local','100x100'),
(29,'Pitch Covers','Manual','2025-08-27','NA','80x100','local','80x100'),
(30,'Pitch Covers','Manual','2025-08-27','NA','70x100','local','70x100'),
(31,'Pitch Covers','Manual','2025-08-27','NA','40x100','local','40x100'),
(32,'Pitch Covers','Manual','2025-08-27','NA','30x100','local','30x100'),
(33,'Pitch Covers','Manual','2025-08-27','NA','20x100','local','20x100'),
(37,'Lawn Mower Outfield','Mechanised','2025-08-27','NA','N/A','Allett Regal 36','Allett Regal 36'),
(38,'Lawn Mower Outfield','Mechanised','2025-08-27','NA','59 Inches','Boroness LM 315','Boronees LM 315'),
(39,'Roller','Manual','2025-08-27','kg','250','local','Manual 250 Kg'),
(40,'TORO 3250- Scarifyer','Mechanised','2025-08-27','NA','00','3250- Scarifyer','TORO 3250- Scarifyer'),
(41,'TORO 1000- Scarifyer','Mechanised','2025-08-27','NA','00','1000- Scarifyer','TORO 1000- Scarifyer'),
(42,'Lawn Mower Outfield','Mechanised','2025-08-27','NA','N/A','TORO 3250','Toro 3250 - 2')

            ]
            
            # Execute the batch insert
            cursor.executemany(sql, data)
            connection.commit()
            print("Data inserted successfully.")
    except Exception as e:
            print(f"An error occurred: {e}")

def addChemicals(org):
    try:
        with connection.cursor() as cursor:
            # Define the table name safely
            table_name = f"{org}_fertilizer_master"
            
            # Updated INSERT query to include "print_details"
            sql = f"""
                INSERT INTO `{table_name}` 
                (chemical_name,chemical_type) 
                VALUES (%s, %s)
            """
            
            # Updated data with 8 values per record
            data = [
             ("13-00-45 (Pottasium Nitrate)", "Fertilizer"),
    ("Bolster (Biostimulant)", "Fertilizer"),
    ( "Griggs MegaAlex (3-0-0)", "Fertilizer"),
    ( "Oberon (Spiromesifen 240 SC) Insecticide", "Insecticide"),
    ("Alliete (Fosetyl Al 80 WP) Fungicide", "Fungicide"),
    ("PIXMA Fungicide  (Carbendabin+Mencozeb)", "Fungicide"),
    ("Endurance Flex", "Fertilizer"),
    ("Calmag", "Fertilizer"),
    ("Premise", "Insecticide"),
    ("Ocean Glas", "Insecticide"),
    ("Amister Top", "Fungicide"),
    ("Thiophanate Mythyl (Theme)", "Fungicide"),
    ("Ammonium Sulphate", "Fertilizer"),
    ("Ferrous Sulphate", "Fertilizer"),
    ("Chlorothalonil (Kawach)", "Fungicide"),
    ("Bavistine", "Fungicide"),
    ("18-01-08", "Fertilizer"),
    ("Fury (Carbofuran)", "Herbicide"),
    ("00-22-42", "Fertilizer"),
    ("30-00-00", "Fertilizer"),
    ("00-00-30", "Fertilizer"),
    ("Bhugold (Tricoderma)", "Fungicide"),
    ("Humicil (Bio-Stimulant)", "Fertilizer"),
    ("TATA Surplus (Micro-Nutrient)", "Fertilizer"),
    ("Isobion (Amino Acid)", "Fertilizer"),
    ("2-4 D", "Herbicide"),
    ("Fern (Bifenthrin)", "Insecticide"),
    ("Tricel (Chloropyrophous)", "Insecticide"),
    ("00-52-34", "Fertilizer"),
    ("4-6-4", "Fertilizer"),
    ("Tricker (Soil Surfectant)", "Fertilizer"),
    ("Sunrise (Selective Herbicide)", "Herbicide"),
    ("00-00-50", "Fertilizer"),
    ("00-52-34", "Fertilizer"),
    ("19-19-19", "Fertilizer"),
    ("20-20-00-13", "Fertilizer"),
    ("Alto (Metsulfuron)", "Fungicide"),
    ("Altosurf (Wetting Agent)", "Fertilizer"),
    ("Cyno (Chlorimuron Ethyl)", "Fungicide"),
    ("Sempra (Halosulfuron)", "Herbicide"),
    ("Streptocycline", "Fungicide"),
    ("TILT (Propiconazole)", "Fungicide"),
    ("Regent Ultra", "Insecticide"),
    ("Abacin (Abamectine)", "Insecticide"),
    ("Ridomil Gold", "Fungicide"),
    ("Virtako (Syngenta)", "Insecticide"),
    ("Trace+ (Folimax)", "Fertilizer"),
    ("GYPSUM", "Fertilizer"),
    ("Dost Super (Pendamythalin)", "Herbicide"),
    ("Round Up (Glyphosate)", "Herbicide")

            ]
            
            # Execute the batch insert
            cursor.executemany(sql, data)
            connection.commit()
            print("Data inserted successfully.")
    except Exception as e:
            print(f"An error occurred: {e}")



def createAllMastersName(instance):
    tables = ["machinery","state","city", "ground", "pitch","match","match_scores","curator_daily_recording","fertilizer","export_log","icc_pitch_report"]
    for t in tables:
        tableName=instance.org_id+"_"+t+"_master"
        masterList=MastersList()
        masterList.org_id=instance.org_id
        masterList.tablename=tableName
        masterList.admin_id=instance
        masterList.auth_scorer=True
        masterList.auth_curator=True
        masterList.auth_groundman=True
        masterList.save()

        createTable(tableName,t,instance.org_id)


def update_admin_user(request, admin_id):
    user = get_object_or_404(AdminUserList, id=admin_id)

    if request.method == 'POST':
        form = AdminUserUpdateForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect('admin_users_list')  # redirect after update
    else:
        form = AdminUserUpdateForm(instance=user)

    return render(request, 'super_admin_user/admin/update_admin_user.html', {'form': form})



def create_admin_user(request):
    try:
        if request.method == 'POST':
            form = AdminUserForm(request.POST, request.FILES)
            if form.is_valid():

                instance=form.save()
                # print(request, 'Admin user created successfully')
                createAllMastersName(instance)

                return redirect('admin_users_list')  # Redirect to a view that lists admin users
            else:
                print(request, 'Please correct the errors below')
        else:
            form = AdminUserForm()
        return render(request, 'super_admin_user/admin/create_admin.html', {'form': form})
    except Exception as e:
        print(e)

def admin_users_list(request):
    admin_users = AdminUserList.objects.all()
    return render(request, 'super_admin_user/admin/admin_users_list.html', {'admin_users': admin_users})

def admin_user_details(request, admin_id):
    admin = AdminUserList.objects.get(id=admin_id)
    return render(request, 'super_admin_user/admin/admin_user_details.html', {'admin': admin})