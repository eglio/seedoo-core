# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

from openerp import SUPERUSER_ID, tools
from openerp.osv import orm, fields, osv
from openerp.tools.translate import _
from util.selection import *

EMPLOYEE_MASK = 100000000
DEPARTMENT_MASK = 200000000

class protocollo_assegnatario(osv.osv):
    _name = 'protocollo.assegnatario'
    _auto = False

    def _dept_name_get_fnc(self, cr, uid, ids, prop, unknow_none, context=None):
        res = self.name_get(cr, uid, ids, context=context)
        return dict(res)

    _columns = {
        'name': fields.function(_dept_name_get_fnc, type='char', string='Name'),
        'nome': fields.char('Nome', size=512, readonly=True),
        'tipologia': fields.selection(TIPO_ASSEGNATARIO_SELECTION, 'Tipologia', readonly=True),
        'employee_id': fields.many2one('hr.employee', 'Dipendente', readonly=True),
        'department_id': fields.many2one('hr.department', 'Dipartimento', readonly=True),
        'parent_id': fields.many2one('protocollo.assegnatario', 'Ufficio di Appartenenza', readonly=True),
        'child_ids': fields.one2many('protocollo.assegnatario', 'parent_id', 'Figli'),
    }

    def name_get(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        if not ids:
            return []
        if isinstance(ids, (int, long)):
            ids = [ids]
        reads = self.read(cr, uid, ids, ['nome','parent_id'], context=context)
        res = []
        for record in reads:
            name = record['nome']
            if record['parent_id']:
                name = record['parent_id'][1]+' / '+name
            res.append((record['id'], name))
        return res

    def init(self, cr):
        tools.sql.drop_view_if_exists(cr, 'protocollo_assegnatario')
        cr.execute("""
            CREATE view protocollo_assegnatario as
              (
                SELECT
                  %s + e.id AS id,
                  e.name_related AS nome,
                  'employee' AS tipologia,
                  e.id AS employee_id,
                  NULL AS department_id,
                  %s + e.department_id AS parent_id
                FROM hr_employee e
                WHERE e.id != %s
              )
              UNION
              (
                SELECT 
                  %s + d.id AS id,
                  d.name AS nome,
                  'department' AS tipologia,
                  NULL AS employee_id,
                  d.id AS department_id,
                  %s + d.parent_id AS parent_id
                FROM hr_department d
                WHERE assignable = TRUE
              )
        """, (EMPLOYEE_MASK, DEPARTMENT_MASK, SUPERUSER_ID, DEPARTMENT_MASK, DEPARTMENT_MASK))



class protocollo_assegnazione(orm.Model):
    _name = 'protocollo.assegnazione'
    _order = 'tipologia_assegnazione'

    _columns = {
        'protocollo_id': fields.many2one('protocollo.protocollo', 'Protocollo', ondelete='cascade'),
        'assegnatario_id': fields.many2one('protocollo.assegnatario', 'Assegnatario'),
        'tipologia_assegnatario': fields.selection(TIPO_ASSEGNATARIO_SELECTION, string='Tipologia Assegnatario'),

        # campi per tipologia assegnatario 'employee'
        'assegnatario_employee_id': fields.many2one('hr.employee', 'Assegnatario (Dipendente)'),
        'assegnatario_employee_department_id': fields.many2one('hr.department', 'Assegnatario (Ufficio del Dipendente)'),

        # campi per tipologia assegnatario 'department'
        'assegnatario_department_id': fields.many2one('hr.department', 'Assegnatario (Ufficio)'),
        'assegnatario_department_parent_id': fields.many2one('hr.department', 'Assegnatario (Ufficio Padre)'),

        'tipologia_assegnazione': fields.selection(TIPO_ASSEGNAZIONE_SELECTION, 'Tipologia Assegnazione'),
        'state': fields.selection(STATE_ASSEGNATARIO_SELECTION, 'Stato'),

        'assegnatore_id': fields.many2one('hr.employee', 'Assegnatore'),
        'assegnatore_department_id': fields.many2one('hr.department', 'Ufficio Assegnatore'),

        'parent_id': fields.many2one('protocollo.assegnazione', 'Assegnazione Ufficio', ondelete='cascade'),
        'child_ids': fields.one2many('protocollo.assegnazione', 'parent_id', 'Assegnazioni Dipendenti'),
    }

    _sql_constraints = [
        ('protocollo_assegnazione_unique', 'unique(protocollo_id, assegnatario_id, tipologia_assegnazione)',
         'Protocollo e Assegnatario con già uno stato nel DB!'),
    ]

    def _crea_assegnazione(self, cr, uid, protocollo_id, assegnatario_id, assegnatore_id, tipologia, parent_id=False):
        assegnatario_obj = self.pool.get('protocollo.assegnatario')
        assegnatario = assegnatario_obj.browse(cr, uid, assegnatario_id)
        assegnatore_obj = self.pool.get('hr.employee')
        assegnatore = assegnatore_obj.browse(cr, uid, assegnatore_id)

        vals = {
            'protocollo_id': protocollo_id,
            'assegnatario_id': assegnatario.id,
            'tipologia_assegnatario': assegnatario.tipologia,
            'tipologia_assegnazione': tipologia,
            'state': 'assegnato',
            'assegnatore_id': assegnatore.id,
            'ufficio_assegnatore_id': assegnatore.department_id.id if assegnatore.department_id else False,
            'parent_id': parent_id
        }
        if assegnatario.tipologia == 'employee':
            vals['assegnatario_employee_id'] = assegnatario.employee_id.id
            vals['assegnatario_employee_department_id'] = assegnatario.employee_id.department_id.id if assegnatario.employee_id.department_id else False
        if assegnatario.tipologia == 'department':
            vals['assegnatario_department_id'] = assegnatario.department_id.id
            vals['assegnatario_department_parent_id'] = assegnatario.department_id.parent_id.id if assegnatario.department_id.parent_id.id else False

        assegnazione_id = self.create(cr, uid, vals)
        return assegnazione_id


    def _crea_assegnazioni(self, cr, uid, protocollo_id, assegnatario_ids, assegnatore_id, tipologia):
        for assegnatario_id in assegnatario_ids:
            assegnazione_id = self._crea_assegnazione(cr, uid, protocollo_id, assegnatario_id,
                                                      assegnatore_id, tipologia)

            dipendente_assegnatario_ids = self.pool.get('protocollo.assegnatario').search(cr, uid, [
                ('parent_id', '=', assegnatario_id),
                ('tipologia', '=', 'employee')
            ])
            for dipendente_assegnatario_id in dipendente_assegnatario_ids:
                self._crea_assegnazione(cr, uid, protocollo_id, dipendente_assegnatario_id,
                                                          assegnatore_id, tipologia, assegnazione_id)


    def salva_assegnazione_competenza(self, cr, uid, protocollo_id, assegnatario_id, assegnatore_id):
        if protocollo_id and assegnatario_id and assegnatore_id:

            assegnazione_ids = self.search(cr, uid, [
                ('protocollo_id', '=', protocollo_id),
                ('tipologia_assegnazione', '=', 'competenza'),
                ('assegnatario_id', '=', assegnatario_id),
                ('parent_id', '=', False)
            ])
            if not assegnazione_ids:
                # eliminazione delle vecchie assegnazioni
                assegnazione_ids = self.search(cr, uid, [
                    ('protocollo_id', '=', protocollo_id),
                    ('tipologia_assegnazione', '=', 'competenza')
                ])
                if assegnazione_ids:
                    self.unlink(cr, uid, assegnazione_ids)

                # creazione della nuova assegnazione
                self._crea_assegnazioni(cr, uid, protocollo_id, [assegnatario_id], assegnatore_id, 'competenza')


    def salva_assegnazione_conoscenza(self, cr, uid, protocollo_id, assegnatario_ids, assegnatore_id, delete=True):
        if protocollo_id and assegnatore_id:

            assegnazione_ids = self.search(cr, uid, [
                ('protocollo_id', '=', protocollo_id),
                ('tipologia_assegnazione', '=', 'conoscenza'),
                ('parent_id', '=', False)
            ])

            assegnatario_to_create_ids = []
            assegnatario_to_unlink_ids = []

            if assegnazione_ids:
                old_assegnatari = self.read(cr, uid, assegnazione_ids, ['assegnatario_id'])
                old_assegnatario_ids = []
                for old_assegnatario in old_assegnatari:
                    old_assegnatario_ids.append(old_assegnatario['assegnatario_id'][0])

                assegnatario_to_create_ids = list(set(assegnatario_ids) - set(old_assegnatario_ids))
                assegnatario_to_unlink_ids = list(set(old_assegnatario_ids) - set(assegnatario_ids))
            else:
                assegnatario_to_create_ids = assegnatario_ids

            if assegnatario_to_unlink_ids and delete:
                # eliminazione delle vecchie assegnazioni (eventuali figli vengono eliminati a cascata)
                assegnazione_to_unlink_ids = self.search(cr, uid, [
                    ('protocollo_id', '=', protocollo_id),
                    ('tipologia_assegnazione', '=', 'conoscenza'),
                    ('assegnatario_id', 'in', assegnatario_to_unlink_ids)
                ])
                if assegnazione_to_unlink_ids:
                    self.unlink(cr, uid, assegnazione_to_unlink_ids)

            if assegnatario_to_create_ids:
                # creazione della nuova assegnazione
                self._crea_assegnazioni(cr, uid, protocollo_id, assegnatario_to_create_ids, assegnatore_id, 'conoscenza')


    def modifica_stato_assegnazione(self, cr, uid, protocollo_ids, state):
        employee_obj = self.pool.get('hr.employee')
        employee_ids = employee_obj.search(cr, uid, [('user_id', '=', uid)])
        if len(employee_ids) == 0:
            raise orm.except_orm('Attenzione!', 'Non è stato trovato il dipendente per la tua utenza!')

        employee_id = employee_ids[0]
        for protocollo_id in protocollo_ids:
            # verifica che il protocollo non abbia uno stato diverso da 'Assegnato'
            assegnazione_state_ids = self.search(cr, uid, [
                ('protocollo_id', '=', protocollo_id),
                ('tipologia_assegnatario', '=', 'employee'),
                ('state', '!=', 'assegnato')
            ])
            if assegnazione_state_ids:
                assegnazione_state = self.browse(cr, uid, assegnazione_state_ids[0])
                for state_assegnatario in STATE_ASSEGNATARIO_SELECTION:
                    if state_assegnatario[0] == assegnazione_state.state:
                        raise orm.except_orm(
                            'Attenzione!',
                            '''
                            Non è più possibile eseguire l\'operazione richiesta!
                            Il protocollo è in stato "%s"!
                            ''' % (str(state_assegnatario[1]),)
                        )
                        break

            # verifica che l'utente sia uno degli assegnatari del protocollo
            assegnazione_ids = self.search(cr, uid, [
                ('assegnatario_employee_id', '=', employee_id),
                ('protocollo_id', '=', protocollo_id),
            ])

            if len(assegnazione_ids) == 0:
                raise orm.except_orm('Attenzione!', 'Non sei uno degli assegnatari del protocollo!')

            # aggiorna il nuovo stato per l'assegnazione dell'utente
            self.write(cr, uid, assegnazione_ids, {'state': state})
            for assegnazione_id in assegnazione_ids:
                # aggiorna, se presente, anche l'assegnazione dell'ufficio
                assegnazione = self.browse(cr, uid, assegnazione_id)
                if assegnazione.parent_id:
                    self.write(cr, uid, [assegnazione.parent_id.id], {'state': state})