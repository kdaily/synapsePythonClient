import synapseclient
import jsonschema

def _rowset_to_dicts(rowset):
    header_names = [x['name'] for x in rowset.headers]
    instances = []
    for row in instances:
        instance = dict([(k,v) for k,v in zip(header_names, row['values']) if v])
        instances.append(instance)
    return instances

def validate_query(syn, query, schema):
    res = syn.tableQuery(query)
    # Get data as rowset to avoid type conversion problems.
    rowset = res.asRowSet()
    instances = _rowset_to_dicts(rowset)
    jsonschema.validate(instance=instances, schema=schema)
