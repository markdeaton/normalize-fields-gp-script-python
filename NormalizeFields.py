# Normalize Fields GP Tool for ArcGIS Desktop
# Author: Mark Deaton (mark4238)
# Inputs:
#   * feature class
#   * fields to normalize (multiple-select, numeric)
#   * field to normalize against (numeric)
#   * new fieldname suffix (default to )

import arcpy
import sys

# Parameter helper function
def getParam(param_num):
    return sys.argv[param_num + 1] #arcpy.GetParameter(param_num)

# Main function, all functions run in NearByGroup
def normalize_fields(in_featureclass, in_field_names, norm_field, new_field_suffix="_norm"):
    # CONSTS
    FIELD_MAP_IN = 0
    FIELD_MAP_OUT = 1
    # Progressor: calculating will probably take much longer than creating fields
    PROGRESSOR_INC_CREATEFIELD = 1
    PROGRESSOR_INC_CALCFIELD = 5

    # This should support all licenses: basic, standard, advanced
    # if arcpy.ProductInfo().lower() not in ['arcinfo']:
    #     arcpy.AddError("An ArcGIS for Desktop Advanced license is required.")
    #     sys.exit()

    PROGRESSOR_MAX_VAL = (len(in_field_names) * PROGRESSOR_INC_CREATEFIELD) + \
                         (len(in_field_names) * PROGRESSOR_INC_CALCFIELD)
    progressor_current_val = 0
    arcpy.SetProgressor('step', '', 0, PROGRESSOR_MAX_VAL)

    existing_fields = arcpy.ListFields(in_featureclass)
    existing_fieldnames = list(map((lambda field: field.name), existing_fields))
    field_map = []

    # Create fields to hold normalized values
    for in_fieldname in in_field_names:
        in_field_idx = existing_fieldnames.index(in_fieldname)
        in_field = existing_fields[in_field_idx]
        norm_fieldname_proposed = in_fieldname + new_field_suffix
        try:
            existing_fieldnames.index(norm_fieldname_proposed)
            # if we continue, the field was found, so we need to keep trying
            for x in range(1, 100):
                norm_fieldname_proposed = in_fieldname + new_field_suffix + str(x)
                existing_fieldnames.index(norm_fieldname_proposed)
            # gotta stop somewhere; if more than 99 exist, throw an error
            arcpy.AddError('Cannot create normalized field for ' + in_fieldname +
                           ' because too many similar fields already exist.' +
                           '\nPlease use a different suffix or delete some fields.')
            sys.exit(0)
        except:  # here we've found an unused field name
            field_map.append([in_field, norm_fieldname_proposed])

    # Add fields to Input
    for field_set in field_map:
        in_field = field_set[FIELD_MAP_IN]
        out_field = field_set[FIELD_MAP_OUT]
        field_type = get_field_type(in_field.type)
        try:
            sStatus = 'Creating normalized field \'' + out_field + '\''
            arcpy.AddMessage(sStatus)
            arcpy.SetProgressorLabel(sStatus)
            res = arcpy.management.AddField(in_featureclass, out_field, field_type,
                                  in_field.precision, in_field.scale, in_field.length)
            progressor_current_val += PROGRESSOR_INC_CREATEFIELD
            arcpy.SetProgressorPosition(progressor_current_val)
        except arcpy.ExecuteError as errExec:
            arcpy.AddError('Error adding field \'' + out_field + '\': ' + errExec.message)
            raise errExec

    # Now all fields for normalized values should exist; do the calculation
    for field_set in field_map:
        out_field = field_set[FIELD_MAP_OUT]
        in_field = field_set[FIELD_MAP_IN].name
        try:
            sStatus = 'Calculating field \'' + out_field + '\''
            arcpy.AddMessage(sStatus)
            arcpy.SetProgressorLabel(sStatus)
            res = arcpy.management.CalculateField(in_featureclass, out_field,
                        'norm(!' + in_field + '!, !' + norm_field + '!)', 'PYTHON',
                        'def norm(infld, normfld):' + '\n\t' + 'if normfld == 0: return None' + '\n\t' +
                        'else: return float(infld) / normfld')
            progressor_current_val += PROGRESSOR_INC_CALCFIELD
            arcpy.SetProgressorPosition(progressor_current_val)
        except arcpy.ExecuteError as errExec:
            arcpy.AddError('Error calculating field \'' + out_field + '\': ' + errExec.message)
            raise errExec


# Field type name remapping is necessary. http://desktop.arcgis.com/en/arcmap/latest/analyze/arcpy-classes/field.htm
def get_field_type(field_type):
    # Actually, since it's division, we'll always create a double field
    return 'DOUBLE'
    # if field_type.lower() == 'integer': return 'LONG'
    # elif field_type.lower() == 'smallinteger': return 'SHORT'
    # else: return field_type


# Run the script
if __name__ == '__main__':

    # Get Parameters
    in_workspace = getParam(0)
    in_fields = getParam(1).split(";") if getParam(1).find(";") > -1 else [
        getParam(1)]
    norm_field = getParam(2)
    new_field_suffix = getParam(3)

    normalize_fields(in_workspace, in_fields, norm_field, new_field_suffix)
    print ("finished")
