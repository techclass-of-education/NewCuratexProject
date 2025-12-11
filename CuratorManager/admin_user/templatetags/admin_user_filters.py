from django import template
from datetime import datetime
register = template.Library()


@register.filter
def to_ddmmyyyy(value):
    try:
        # first try python date/datetime object
        return value.strftime("%d-%m-%Y")
    except:
        pass

    try:
        # if string "YYYY-MM-DD"
        dt = datetime.strptime(str(value), "%Y-%m-%d")
        return dt.strftime("%d-%m-%Y")
    except:
        return value  # fallback



@register.filter
def concat(value, arg):
    return f"{value}{arg}"


@register.filter
def split_by_delimiter(value, delimiter="__####__"):
    if value:
        if delimiter in value:
            values=value.split(delimiter)
            val=[]
            for i in range(len(values)):
                val.append(values[i].strip("_#").strip())
            return val
                
        else:
            return [value.strip("_#").strip()]
    else:
        return []
        


@register.filter
def split_by_delimiter_doller(value, delimiter="$##$"):
    if value:
        if delimiter in value:
            return value.split(delimiter)
        else:
            return [value]
    else:
        return []
    
