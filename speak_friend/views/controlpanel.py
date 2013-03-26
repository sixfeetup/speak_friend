# Views related to configuring options for the site.
from collections import OrderedDict

from colander import MappingSchema
from deform import Form, ValidationFailure
from pyramid.httpexceptions import HTTPMethodNotAllowed
from pyramid.view import view_defaults

from speak_friend.models.controlpanel import ControlPanelSection


@view_defaults(route_name='control_panel')
class ControlPanel(object):
    def __init__(self, request):
        self.request = request
        self.sections = self.request.registry.get('controlpanel', {})
        self.saved_sections = self.get_sections()
        self.section_forms = OrderedDict()
        sorted_sections = sorted(self.sections.items(),
                                 key=lambda x:x[0].title,
                                 reverse=True)
        for section_name, section_schema in sorted_sections:
            section_form = Form(
                section_schema,
                buttons=('submit', 'cancel'),
                formid=section_name,
            )
            self.section_forms[section_name] = section_form

    def post(self):
        if self.request.method != "POST":
            return HTTPMethodNotAllowed()
        if 'submit' not in self.request.POST:
            return self.get()
        html = []
        posted_formid = self.request.POST['__formid__']
        for (formid, form) in self.section_forms.items():
            if formid == posted_formid:
                try:
                    controls = self.request.POST.items()
                    captured = form.validate(controls)
                    html.append(form.render(captured))
                    self.save_section(formid, captured)
                except ValidationFailure as e:
                    # the submitted values could not be validated
                    html.append(e.render())
            else:
                html.append(self.get_rendered_form(form))

        return {
            'forms': self.section_forms.values(),
            'rendered_form': ''.join(html),
        }

    def get(self):
        html = [
            self.get_rendered_form(form)
            for form in self.section_forms.values()
        ]

        return {
            'forms': self.section_forms.values(),
            'rendered_form': ''.join(html),
        }

    def get_rendered_form(self, form):
        record = self.saved_sections.get(form.formid, None)
        appstruct = record_to_appstruct(record)
        return form.render(appstruct.get('panel_values', {}))

    def save_section(self, formid, captured):
        cp_section = self.saved_sections.get(formid, None)
        if cp_section is None:
            cp_section = ControlPanelSection(
                section=formid,
                panel_path=self.sections[formid].path,
                panel_values=captured
            )
        else:
            cp_section.panel_values = captured
        self.request.db_session.merge(cp_section)

    def get_sections(self):
        query = self.request.db_session.query(ControlPanelSection)
        qry_filter = ControlPanelSection.section.in_(self.sections.keys())
        return dict([
            (cp_section.section, cp_section)
            for cp_section in query.filter(qry_filter).all()
        ])

    def get_value(self, section_name, setting, default=None):
        current = self.saved_sections.get(section_name)
        if current and current.panel_values:
            return current.panel_values.get(setting, default)
        elif current:
            for child in current.schema.children:
                if child.name == setting:
                    return child.default
        elif section_name in self.sections:
            for child in self.sections[section_name].children:
                if child.name == setting:
                    return child.default
        return default


def record_to_appstruct(self):
    if self is None:
        return {}
    return dict([
        (k, self.__dict__[k])
        for k in sorted(self.__dict__) if '_sa_' != k[:4]
    ])
