#  import os
from ocrd.constants import NAMESPACES as NS, TAG_METS_AGENT, TAG_METS_NAME

from .ocrd_xml_base import ET

class OcrdAgent(object):
    """
    Represents a <mets:agent>
    """

    #  @staticmethod
    #  from_el(el):
    #      role = el_agent.get('ROLE')
    #      agent_type = el_agent.get('TYPE')
    #      otherrole = el_agent.get('OTHERROLE')
    #      name_parts = string.split(el.find('mets:name', NS).text, ' ', 2)
    #      #  name = name_parts[0]
    #      #  version = name_parts[1][1:]     # v0.0.1 => 0.0.1
    #      return OcrdAgent(el, name, role, agent_type, otherrole)

    def __init__(self, el=None, name=None, agent_type=None, role=None, otherrole=None):
        if el is None:
            el = ET.Element(TAG_METS_AGENT)
        self._el = el
        self.name = name
        self.type = agent_type
        self.role = role
        self.otherrole = otherrole

    def __str__(self):
        props = ', '.join([
            '='.join([k, getattr(self, k) if getattr(self, k) else '---'])
            for k in ['role', 'otherrole', 'name']
        ])
        return '<OcrdAgent [' + props + ']/> '

    @property
    def type(self):
        return self._el.get('TYPE')

    @type.setter
    def type(self, agent_type):
        if agent_type is not None:
            self._el.set('TYPE', agent_type)

    @property
    def role(self):
        return self._el.get('ROLE')

    @role.setter
    def role(self, role):
        if role is not None:
            self._el.set('ROLE', role)

    @property
    def otherrole(self):
        return self._el.get('OTHERROLE')

    @otherrole.setter
    def otherrole(self, otherrole):
        if otherrole is not None:
            self._el.set('ROLE', 'OTHER')
            self._el.set('OTHERROLE', otherrole)

    @property
    def name(self):
        el_name = self._el.find('mets:name', NS)
        if el_name is not None:
            return el_name.text

    @name.setter
    def name(self, name):
        if name is not None:
            el_name = self._el.find('mets:name', NS)
            if el_name is None:
                el_name = ET.SubElement(self._el, TAG_METS_NAME)
            el_name.text = name
