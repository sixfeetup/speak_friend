# Views related to configuring options for the site.

from colander import MappingSchema
from deform import Form, ValidationFailure

from speak_friend.models import DBSession
from speak_friend.models.controlpanel import ControlPanel


# FIXME: attach appropriate permissions
def control_panel(request):
    sections = request.registry.get('controlpanel', {})
    section_forms = {}
    css_resources = []
    js_resources = []
    session = DBSession()
    query = session.query(ControlPanel)
    qry_filter = ControlPanel.section.in_(sections.keys())
    saved_sections = query.filter(qry_filter)
    saved_sections = dict([
        (cp_section.section, cp_section)
        for cp_section in saved_sections.all()
    ])
    for section_name, section_schema in sections.items():
        section_form = Form(
            section_schema,
            buttons=('submit', 'cancel'),
            formid=section_name,
        )
        section_forms[section_name] = section_form
        resources = section_form.get_widget_resources()
        css_resources.extend([
            'deform:static/%s' % css_path
            for css_path in resources['css']
        ])
        js_resources.extend([
            'deform:static/%s' % js_path
            for js_path in resources['js']
        ])

    html = []
    if 'submit' in request.POST:
        posted_formid = request.POST['__formid__']
        for (formid, form) in section_forms.items():
            if formid == posted_formid:
                try:
                    controls = request.POST.items()
                    captured = form.validate(controls)
                    html.append(form.render(captured))
                    cp_section = saved_sections.get(formid, None)
                    if cp_section is None:
                        cp_section = ControlPanel(
                            section=formid,
                            panel_path=sections[formid].path,
                            panel_values=captured
                        )
                    else:
                        cp_section.panel_values = captured
                    session.merge(cp_section)
                except ValidationFailure as e:
                    # the submitted values could not be validated
                    html.append(e.render())
            else:
                appstruct = record_to_appstruct(saved_sections.get(formid,
                                                                   None))
                html.append(form.render(appstruct.get('panel_values', {})))
    else:
        for form in section_forms.values():
            appstruct = record_to_appstruct(saved_sections.get(form.formid,
                                                               None))
            html.append(form.render(appstruct.get('panel_values', {})))

    return {
        'css_resources': css_resources,
        'js_resources': js_resources,
        'form': ''.join(html),
    }


def record_to_appstruct(self):
    if self is None:
        return {}
    return dict([
        (k, self.__dict__[k])
        for k in sorted(self.__dict__) if '_sa_' != k[:4]
    ])
