# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

import logging
from openerp.osv import fields, osv, orm
from openerp.tools.translate import _
import datetime


_logger = logging.getLogger(__name__)


class protocollo_archivio_wizard(osv.TransientModel):
    """
        A wizard to manage the creation of Archivio Protocollo
    """
    STATE_SELECTION = [
        ('none', 'Nessuna archiviazione'),
        ('date', 'Intervallo per data'),
        ('number', 'Intervallo per numero'),
    ]

    _name = 'protocollo.archivio.wizard'
    _description = 'Crea Archivio Protocollo'

    def get_protocol_year(self, cr, uid, context=None):
        protocollo_archivio_obj = self.pool.get('protocollo.archivio')
        archivio_ids = protocollo_archivio_obj._get_archivio_ids(cr, uid, True)
        archivio_ids_str = ', '.join(map(str, archivio_ids))
        aoo_id = self.get_default_aoo_id(cr, uid, [])
        cr.execute('''
                     SELECT DISTINCT(pp.year)
                     FROM protocollo_protocollo pp
                     WHERE pp.aoo_id = %s
                            AND pp.archivio_id IN (''' + archivio_ids_str + ''')
                 ''', (aoo_id,))
        year_res = []
        [year_res.append((res[0], res[0])) for res in cr.fetchall()]
        return year_res

    _columns = {
        'name': fields.char('Nome Archivio', size=256, required=True, readonly=False),
        'aoo_id': fields.many2one('protocollo.aoo', 'AOO', required=True, readonly=True),
        'interval_type': fields.selection(STATE_SELECTION, 'Tipo di intervallo', required=True),
        'date_start': fields.datetime('Data Inizio', required=False),
        'date_end': fields.datetime('Data Fine', required=False),
        'year_start': fields.selection(get_protocol_year, 'Anno Inizio', required=False),
        'year_end': fields.selection(get_protocol_year, 'Anno Fine', required=False),
        'protocol_start': fields.char('Protocollo Inizio', required=False),
        'protocol_end': fields.char('Protocollo Fine', required=False),
    }

    def _get_default_name(self, cr, uid, wizard):
        #TODO
        return "Archivio di Deposito"


    def get_default_protocol_start(self, cr, uid, wizard):
        protocollo_obj = self.pool.get('protocollo.protocollo')
        protocollo_archivio_obj = self.pool.get('protocollo.archivio')
        aoo_id = self.get_default_aoo_id(cr, uid, [])
        archivio_corrente = protocollo_archivio_obj._get_archivio_ids(cr, uid, True)
        start_protocol_ids = protocollo_obj.search(cr, uid, [
            ('aoo_id', '=', aoo_id),
            ('state', 'in', ['registered', 'notified', 'sent', 'waiting', 'error', 'canceled']),
            ('archivio_id', '=', archivio_corrente)
        ], order='name asc', limit=1)
        if len(start_protocol_ids) > 0:
            start_protocol = protocollo_obj.browse(cr, uid, start_protocol_ids[0])
            return start_protocol.name
        return 0

    def get_default_protocol_end(self, cr, uid, wizard):
        protocollo_obj = self.pool.get('protocollo.protocollo')
        protocollo_archivio_obj = self.pool.get('protocollo.archivio')
        aoo_id = self.get_default_aoo_id(cr, uid, [])
        archivio_corrente = protocollo_archivio_obj._get_archivio_ids(cr, uid, True)
        start_protocol_ids = protocollo_obj.search(cr, uid, [
            ('aoo_id', '=', aoo_id),
            ('state', 'in', ['registered', 'notified', 'sent', 'waiting', 'error', 'canceled']),
            ('archivio_id', '=', archivio_corrente)
        ], order='name desc', limit=1)
        if len(start_protocol_ids) > 0:
            start_protocol = protocollo_obj.browse(cr, uid, start_protocol_ids[0])
            return start_protocol.name

    def get_default_aoo_id(self, cr, uid, wizard):
        aoo_ids = self.pool.get('protocollo.aoo').search(cr, uid, [])
        for aoo_id in aoo_ids:
            check = self.pool.get('protocollo.aoo').is_visible_to_protocol_action(cr, uid, aoo_id)
            if check:
                return aoo_id
        return False

    _defaults = {
        'name': _get_default_name,
        'interval_type': 'none',
        'aoo_id': get_default_aoo_id,
        'protocol_start': get_default_protocol_start,
        'protocol_end': get_default_protocol_end,
    }

    def action_create(self, cr, uid, ids, context=None):
        protocollo_ids = []
        wizard = self.browse(cr, uid, ids[0], context)
        protocollo_obj = self.pool.get('protocollo.protocollo')
        protocollo_archivio_obj = self.pool.get('protocollo.archivio')
        archivio_corrente = protocollo_archivio_obj._get_archivio_ids(cr, uid, True)
        archivio_ids_str = ', '.join(map(str, archivio_corrente))
        if wizard.name and wizard.aoo_id and wizard.interval_type:

            if wizard.interval_type == 'date':
                if wizard.date_start > wizard.date_end:
                    raise orm.except_orm(_("Avviso"), _("La data di fine deve essere successiva alla data di inizio"))

                # if wizard.number <= 0:
                #     raise orm.except_orm(_("Avviso"), _("Il numero di protocolli deve essere maggiore di 0"))

                protocollo_ids = protocollo_obj.search(cr, uid, [
                    ('aoo_id', '=', wizard.aoo_id.id),
                    ('state', 'in', ['registered', 'notified', 'sent', 'waiting', 'error', 'canceled']),
                    ('registration_date', '>', wizard.date_start),
                    ('registration_date', '<', wizard.date_end),
                    ('archivio_id', '=', archivio_corrente)
                ])
            elif wizard.interval_type == 'number':
                protocol_start_ids = protocollo_obj.search(cr, uid, [('aoo_id', '=', wizard.aoo_id.id), ('name', '=', wizard.protocol_start)])
                protocol_end_ids = protocollo_obj.search(cr, uid, [('aoo_id', '=', wizard.aoo_id.id), ('name', '=', wizard.protocol_start)])

                if len(protocol_start_ids) != 1 or len(protocol_end_ids) != 1:
                    raise orm.except_orm(_("Avviso"), _("Il numero dell'ultimo protocollo deve essere successivo a quello di inizio"))

                cr.execute('''
                                SELECT DISTINCT(pp.id)
                                FROM protocollo_protocollo pp
                                WHERE 
                                    pp.aoo_id = %s AND 
                                    pp.state IN ('registered', 'notified', 'sent', 'waiting', 'error', 'canceled') AND
                                    pp.archivio_id IN (''' + archivio_ids_str + ''') AND
                                    (
                                        (pp.year=%s AND pp.name >= %s) OR pp.year > %s) 
                                        AND (
                                        (pp.year=%s AND pp.name <= %s) OR pp.year < %s
                                    )
                            ''', (wizard.aoo_id.id,
                                  wizard.year_start, wizard.protocol_start, wizard.year_start,
                                  wizard.year_end, wizard.protocol_end, wizard.year_end))

                protocollo_ids = [res[0] for res in cr.fetchall()]

            vals = {
                'name': wizard.name,
                'aoo_id': wizard.aoo_id.id,
                'is_current': False,
                'date_start': wizard.date_start,
                'date_end': wizard.date_end,
            }
            protocollo_archivio_id = protocollo_archivio_obj.create(cr, uid, vals)

            if wizard.interval_type in ('date', 'number'):
                if len(protocollo_ids) == 0:
                    raise orm.except_orm(_("Avviso"), _("Nessun protocollo presente in archivio corrente nell\'intervallo selezionato"))
                if protocollo_archivio_id:
                    protocollo_obj.write(cr, uid, protocollo_ids, {'archivio_id': protocollo_archivio_id}, context=context)

            return {
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'protocollo.emergency.registry',
                'res_id': protocollo_archivio_id,
                'type': 'ir.actions.act_window',
                'context': context,
            }

        return {'type': 'ir.actions.act_window_close'}