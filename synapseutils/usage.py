"""Utilities for gathering usage information about things in Synapse.

"""

import collections
from urllib.parse import quote

import synapseclient
import synapseclient.team


def get_user_group_headers_batch(syn, ids):
    """Get users or teams in batch from their IDs.

    Parameters
    ----------
    :param syn: A synapseclient.Synapse object - Must be logged into Synapse
    :param ids: A list of team or user IDs
    """
    
    uri = '/userGroupHeaders/batch?ids=%s' % quote(",".join(map(str, ids)))
    return [synapseclient.team.UserGroupHeader(**result) for result in syn.restGET(uri)['children']]

def combine_resourceAccess(resourceAccess):
    """Take a list of resourceAccess objects and combine them per individual, concatenating their access types.
    """
    resource_access_dict = collections.defaultdict(dict)
    for ra in resourceAccess:
        curr = resource_access_dict[str(ra['principalId'])]
        curr['principalId'] = ra['principalId']
        try:
            curr['accessType'] = list(set(curr['accessType']).union(set(ra['accessType'])))
        except KeyError:
            curr['accessType'] = ra['accessType']

        resource_access_dict[str(ra['principalId'])] = curr

    return resource_access_dict

    
def get_users_from_acl(syn, acl):      
    """Get all user permissions out of an ACL.

    Expands all teams to individual members, and finds the union of users' permissions.

    Parameters
    ----------
    :param syn: A synapseclient.Synapse object - Must be logged into Synapse
    :param acl: An ACL object from synapseclient.Synapse._getACL.
    """

    user_permissions = []

    principal_ids = [resourceAccess['principalId'] for resourceAccess in acl['resourceAccess']]
    principals = get_user_group_headers_batch(syn, principal_ids)

    resourceAccess_dict = {str(x['principalId']): x for x in acl['resourceAccess']}

    users_resourceAccess_dict = {}

    for principal in principals:

        if principal['ownerId'] in [synapseclient.PUBLIC, synapseclient.AUTHENTICATED_USERS]:
            pass

        curr_accessType = resourceAccess_dict[principal['ownerId']]
        if principal['isIndividual']:
            user_permissions.append(curr_accessType)
        else:
            team_members = syn.getTeamMembers(principal['ownerId'])
            for member in team_members:
                new_accessType = curr_accessType.copy()

                # replace the principal ID of the team with that of the individual
                new_accessType['principalId'] = member['member']['ownerId']
                user_permissions.append(new_accessType)

    return user_permissions

def getEntityPermissions(syn, entity):
    """Get entity permissions for users on the ACL.
    
    Parameters
    ----------
    syn : synapseclient.Synapse
        A synapse client object that has logged in.
    entity : Synapse entity.
        A Synapse entity object or entity ID.
    """

    acl = syn._getACL(entity)
    
    user_perms = get_users_from_acl(syn, acl)

    user_perms = combine_resourceAccess(user_perms)

    return user_perms.values()
