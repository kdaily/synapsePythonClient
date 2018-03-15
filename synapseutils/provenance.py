"""Utilities for Synapse provenance.

This module creates Provenance documents which capture the activity and attribution for a Synapse entity.

The resulting document can be displayed as [PROV-N](http://www.w3.org/TR/prov-n/) or [PROV-JSON](https://www.w3.org/Submission/prov-json/).

"""

import sys

import synapseclient

try:
    import prov.model
# used to catch ImportError, but other errors can happen (see SYNPY-177)
except:
    sys.stderr.write("""\n\nprov not installed!\n
    The synapseclient package recommends but doesn't require the
    installation of prov. If you'd like to use prov,
    refer to the installation instructions at:
      http://prov.readthedocs.io/en/latest/.
    \n\n\n""")
    raise

class SynapseProvenanceDocument(object):
    """Representation of provenance for a Synapse Entity.

    """

    # prov_doc = SYNAPSE

    def __init__(self, syn, e, annotations=[], *args, **kwargs):

        self.syn = syn

        self.prov_doc = self.make_prov_doc()

        self.entity = self.syn.get(e, downloadFile=False)
        self.activity = self.syn.getProvenance(self.entity)

        self._agents = {}
        self._entities = {}
        self._entities["%s.%s" % (self.entity.id, self.entity.versionNumber)] = self.entity
        self._annotations = annotations
        self.set_provenance()

    def set_provenance(self):
        keys = set(self._annotations).intersection(self.entity.annotations.keys())
        annots = {"Entity:%s" % k: (self.entity.annotations[k][0] if type(self.entity.annotations[k]) is list else self.entity.annotations[k]) for k in keys}
        annots['prov:label'] = self.entity.name

        self.prov_entity = self.prov_doc.entity('Entity:%s.%s' % (self.entity.properties.id, self.entity.properties.versionNumber),
                                                annots)

        user = syn.getUserProfile(self.activity['createdBy'])
        agentAnnots = {'agent:userName': user['username'],
                       'agent:displayName': user['displayName']}

        agent = self.prov_doc.agent('User:%s' % self.activity['createdBy'], agentAnnots)

        self._agents[self.activity['createdBy']] = agent

        self.prov_doc.wasAttributedTo(self.prov_entity, self._agents[self.activity['createdBy']])

        self._addUsedEntites()

        self.prov_activity = self.prov_doc.activity('Activity:%s' % self.activity['id'],
                                                   startTime=self.activity['createdOn'],
                                                   endTime=self.activity['createdOn'])

        self.prov_doc.wasGeneratedBy(self.prov_entity, self.prov_activity)

        for key, value in self._used_entities.iteritems():
            self.prov_doc.used(self.prov_activity, value)

    @staticmethod
    def make_prov_doc():
        doc = prov.model.ProvDocument()
        doc.add_namespace('Entity', '/entity/')
        doc.add_namespace('User', '/userProfile/')
        doc.add_namespace('Activity', '/activity/')
        return doc

    def _addUsedEntites(self):

        self._used_entities = {}

        for x in self.activity['used']:
            try:
                _id = "%s.%s" % (x['reference']['targetId'], x['reference']['targetVersionNumber'])
            except KeyError as e:
                sys.stderr.write(str(e))
                continue

            try:
                tmp = self.syn.get(x['reference']['targetId'], version=x['reference']['targetVersionNumber'],
                              downloadFile=False)
                keys = set(self._annotations).intersection(tmp.annotations.keys())
                annots = {"Entity:%s" % k: (tmp.annotations[k][0] if type(tmp.annotations[k]) is list else tmp.annotations[k]) for k in keys}
            except synapseclient.exceptions.SynapseHTTPError as e:
                print e
                continue

            self._used_entities[_id] = self.prov_doc.entity('Entity:%s.%s' % (x['reference']['targetId'], x['reference']['targetVersionNumber']),
                                                            annots)

            try:
                tmp_agent = self._agents[tmp.properties['createdBy']]
            except KeyError:
                user = syn.getUserProfile(tmp.properties['createdBy'])
                tmpAnnots = {'agent:userName': user['username'],
                               'agent:displayName': user['displayName']}
                tmp_agent = self.prov_doc.agent('User:%s' % tmp.properties['createdBy'], tmpAnnots)

            self.prov_doc.wasAttributedTo(self._used_entities[_id], tmp_agent)

    def to_prov(self):
        return self.prov_doc.get_provn()

    def serialize(self, *args, **kwargs):
        return self.prov_doc.serialize(*args, **kwargs)

def _safeGetProvenance(syn, x):
    try:
        return self.syn.getProvenance(x)
    except synapseclient.exceptions.SynapseHTTPError:
        return None
