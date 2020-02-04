# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

{
    "name": "Seedoo Protocollo",
    "version": "8.0.1.8.10",
    "category": "Document Management",
    "summary": "Protocollo Informatico PA",
    "sequence": "1",
    "author": "Agile Business Group, Innoviu, Flosslab",
    "website": "http://www.seedoo.it",
    "license": "AGPL-3",
    "depends": [
        "base",
        "web",
        "l10n_it_pec",
        "sharedmail",
        "document",
        "hr",
        "email_template",
        "report_webkit",
        "seedoo_gedoc",
        "l10n_it_pec_messages",
        "l10n_it_ipa",
        "m2o_tree_widget",
        "m2m_tree_widget",
        "web_pdf_widget",
        "web_dashboard_tile",
        "web_dashboard_tile_mode",
        "password_security"
    ],
    'init_xml': [
        'data/res.country.state.csv',
    ],
    "data": [
        "data/protocollo_company.xml",
        "data/protocollo_configuration.xml",
        "data/protocollo_conferma_template.xml",
        "data/protocollo_annullamento_template.xml",
        "security/protocollo_security.xml",
        "security/protocollo_visibility_security.xml",
        "data/protocollo_profile.xml",
        "security/security_rules.xml",
        "security/password_security_rules.xml",
        "security/ir.model.access.csv",
        "data/protocollo_sequence.xml",
        "data/protocollo_aoo.xml",
        "data/protocollo_typology.xml",
        "data/protocollo_admin.xml",
        "data/protocollo_department.xml",
        "data/protocollo_user_employee.xml",
        "data/ir_config_parameter.xml",
        "gedoc/data/gedoc_data.xml",
        "wizard/create_protocollo_wizard_view.xml",
        "wizard/cancel_protocollo_wizard_view.xml",
        "wizard/modify_protocollo_wizard_view.xml",
        "wizard/aggiungi_classificazione_protocollo_wizard_view.xml",
        "wizard/aggiungi_fascicolazione_protocollo_wizard_view.xml",
        "wizard/aggiungi_assegnatari_protocollo_wizard_view.xml",
        "wizard/aggiungi_assegnatari_conoscenza_protocollo_wizard_view.xml",
        "wizard/riassegna_protocollo_wizard_view.xml",
        "wizard/create_protocollo_mailpec_wizard_view.xml",
        "wizard/modify_protocollo_email_wizard_view.xml",
        "wizard/modify_protocollo_pec_wizard_view.xml",
        "wizard/rifiuta_protocollo_wizard_view.xml",
        "wizard/carica_documenti_wizard_view.xml",
        #"wizard/carica_allegati_wizard_view.xml",
        "wizard/carica_allegato_wizard_view.xml",
        "wizard/registration_protocollo_wizard_view.xml",
        "wizard/confirm_operation_wizard_view.xml",
        "wizard/aggiungi_sender_internal_wizard_view.xml",
        "wizard/create_protocollo_archivio_wizard_view.xml",
        "view/protocollo_sender_receiver_view.xml",
        "wizard/create_mittente_destinatario_wizard_view.xml",
        "wizard/create_destinatari_da_gruppo_wizard_view.xml",
        "wizard/segna_come_letto_protocollo_wizard_view.xml",

        "templates/journal.xml",

        "view/journal.xml",

        "view/res_config.xml",
        "view/partner_view.xml",
        "view/offices_view.xml",
        "view/res_users_view.xml",
        "view/ir_attachment_view.xml",
        "view/protocollo_assegnazione_view.xml",
        "view/protocollo_view.xml",
        "view/protocollo_aoo_view.xml",
        "view/protocollo_archivio_view.xml",
        "view/mail_pec_view.xml",
        "view/sharedmail_view.xml",
        "view/fetchmail_view.xml",
        "view/ir_mail_server_view.xml",
        "view/email_template_view.xml",
        # "view/contact_view.xml",
        "view/report_view.xml",
        "view/menu_item.xml",
        "view/res_groups_view.xml",
        "gedoc/view/gedoc_view.xml",
        "wizard/create_journal_wizard_view.xml",
        "wizard/create_emergency_registry_wizard_view.xml",
        "workflow/protocollo_workflow.xml",
        "data/protocollo_report.xml",
        "menu/menu.xml",
        "data/protocollo_tile.xml",
        "view/protocollo_dashboard_view.xml",
        "view/tile.xml",
        "view/protocollo_profile_view.xml",
        "static/src/xml/upload_override.xml",
        "view/res_partner_view.xml",
        "data/auth_signup_data.xml",
    ],
    "demo": [

    ],
    "qweb": [
        "static/src/xml/base.xml",
        #"static/src/xml/mail.xml",
    ],
    "css": [
        "static/src/css/protocollo.css",
    ],
    "js": [
        "static/src/js/protocollo_accordion.js",
        "static/src/js/protocollo_patch.js",
        "static/src/js/fix_upload.js",
    ],
    "installable": True,
    "application": True,
    "active": False
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
