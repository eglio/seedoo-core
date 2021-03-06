# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import tools, api
from openerp.osv import fields, osv, orm
import logging
import time
import datetime

_logger = logging.getLogger(__name__)
MAX_POP_MESSAGES = 50



class fetchmail_server(osv.osv):
    _inherit = 'fetchmail.server'

    _columns = {
        'move_processed_emails': fields.boolean('Sposta le email processate sulla mailbox'),
        'email_account': fields.selection([
            ('gmail', 'Gmail'), ('aruba', 'Aruba'), ('legalmail', 'Legalmail'), ('other', 'Altro')
        ], 'Provider'),
        'processed_folder': fields.char('Percorso folder email processate'),
        'error_folder': fields.char('Percorso folder email errore'),
        'fetchmail_server_history_ids': fields.one2many('fetchmail.server.history', 'fetchmail_server_id', 'Storico', readonly=True),
    }

    _defaults = {
        'move_processed_emails': False,
        'original': True
    }

    def fetch_mail(self, cr, uid, ids, context=None):
        """WARNING: meant for cron usage only - will commit() after each email!"""
        context = dict(context or {})
        context['fetchmail_cron_running'] = True
        mail_thread = self.pool.get('mail.thread')
        action_pool = self.pool.get('ir.actions.server')
        for server in self.browse(cr, uid, ids, context=context):
            _logger.debug('start checking for new emails on %s server %s', server.type, server.name)
            context.update({'fetchmail_server_id': server.id, 'server_type': server.type})
            error_description = ''
            datetime_start = datetime.datetime.now()
            count, failed = 0, 0
            imap_server = False
            pop_server = False
            if server.type == 'imap':
                try:
                    imap_server = server.connect()
                    imap_server.select()
                    result, data = imap_server.uid('search', None, '(UNSEEN)')
                    for num in data[0].split():
                        exception = False
                        res_id = None
                        result, data = imap_server.uid('fetch', num, '(RFC822)')
                        imap_server.uid('store', num, '-FLAGS', '(\\Seen)')
                        try:
                            res_id = mail_thread.message_process(cr, uid, server.object_id.model,
                                                                 data[0][1],
                                                                 save_original=server.original,
                                                                 strip_attachments=(not server.attach),
                                                                 context=context)
                            imap_server.uid('store', num, '+FLAGS', '(\\Seen)')
                        except Exception as e:
                            exception = True
                            if e.message:
                                error_description += '- ' + e.message + '\n'
                            else:
                                error_description += '- Failed to process mail\n'
                            _logger.exception('Failed to process mail from %s server %s.', server.type, server.name)
                            failed += 1

                        ################################################################################################
                        if server.move_processed_emails:
                            folder_name = server.processed_folder
                            if exception:
                                folder_name = server.error_folder
                            folder_name = self._get_folder_path(server, folder_name)

                            rv, resp, exception_copy_description = None, None, None
                            try:
                                # copia della email dalla inbox alla cartella configurata
                                rv, resp = imap_server.uid('copy', num, folder_name)
                            except Exception as exception_copy:
                                if exception_copy.message:
                                    exception_copy_description = exception_copy.message
                                else:
                                    exception_copy_description = 'Failed to copy mail'
                                _logger.exception('Failed to copy mail from %s server %s: %s', server.type, server.name, str(exception_copy))

                            if rv == 'OK':
                                try:
                                    # eliminazione della email dalla inbox
                                    imap_server.uid('store', num, '+FLAGS', '(\\Deleted)')
                                except Exception as exception_delete:
                                    if exception_delete.message:
                                        exception_copy_description = exception_delete.message
                                    else:
                                        exception_copy_description = 'Failed to delete mail'
                                    _logger.exception('Failed to delete mail from %s server %s: %s', server.type, server.name, str(exception_delete))

                                if not exception_copy_description:
                                    try:
                                        imap_server.expunge()
                                    except Exception as exception_expunge:
                                        # se viene generato un errore durante un expunge non dovrebbe generare nessun
                                        # problema (almeno non è stato evidenziato nei test fatti): infatti la email
                                        # risulta comunque eliminata dalla cartella inbox. Per questo motivo,
                                        # attualmente non facciamo nessuna gestione dell'errore
                                        _logger.exception('Failed to expunge mail from %s server %s: %s', server.type, server.name, str(exception_expunge))
                            elif not exception_copy_description:
                                exception_copy_description = str(resp)
                                _logger.exception("Error in %s server %s: %s", server.type, server.name, str(resp))

                            if exception_copy_description:
                                # si è verificata una eccezione durante la procedura di spostamento della email, quindi
                                # è necessario rimettere la email come non letta e fare il rollback di quanto salvato
                                # nel db
                                try:
                                    imap_server.uid('store', num, '-FLAGS', '(\\Seen)')
                                    if not exception:
                                        failed += 1
                                    error_description += '- ' + exception_copy_description + '\n'
                                    cr.rollback()
                                    continue
                                except Exception as exception_seen:
                                    # si è verificata una eccezione mentre si cercava di mettere la email in non letta,
                                    # essendo un caso limite porta a delle diverse conseguenze a secondo del punto in
                                    # cui è stata generata la prima eccezione (in tutti i casi la email sarà comunque
                                    # salvata su seedoo):
                                    # - exception_copy: questo è il caso peggiore perché la email rimarrà nella inbox
                                    # come letta ma non sarà spostata in nessuna cartella
                                    # - exception_delete: la email rimarrà nella inbox come letta ma sarà spostata
                                    # nella cartella
                                    # - exception_delete: la email rimarrà nella inbox come letta ma sarà spostata
                                    # nella cartella
                                    _logger.exception('Failed to remove flag seen from %s server %s: %s', server.type, server.name, str(exception_seen))
                        ################################################################################################

                        if res_id and server.action_id:
                            action_pool.run(cr, uid, [server.action_id.id], {'active_id': res_id, 'active_ids': [res_id], 'active_model': context.get("thread_model", server.object_id.model)})

                        cr.commit()
                        if not exception:
                            count += 1
                    _logger.debug("Fetched %d email(s) on %s server %s; %d succeeded, %d failed.", (count + failed), server.type, server.name, count, failed)
                except Exception as e:
                    error_description += '- ' + str(e) + '\n'
                    _logger.exception("General failure when trying to fetch mail from %s server %s.", server.type, server.name)
                finally:
                    if imap_server:
                        imap_server.close()
                        imap_server.logout()


            elif server.type == 'pop':
                try:
                    while True:
                        pop_server = server.connect()
                        (numMsgs, totalSize) = pop_server.stat()
                        pop_server.list()
                        for num in range(1, min(MAX_POP_MESSAGES, numMsgs) + 1):
                            (header, msges, octets) = pop_server.retr(num)
                            msg = '\n'.join(msges)
                            res_id = None
                            try:
                                res_id = mail_thread.message_process(cr, uid, server.object_id.model,
                                                                     msg,
                                                                     save_original=server.original,
                                                                     strip_attachments=(not server.attach),
                                                                     context=context)
                                pop_server.dele(num)
                                count += 1
                            except Exception as e:
                                error_description += '- ' + str(e) + '\n'
                                _logger.exception('Failed to process mail from %s server %s.', server.type, server.name)
                                failed += 1
                            if res_id and server.action_id:
                                action_pool.run(cr, uid, [server.action_id.id], {'active_id': res_id, 'active_ids': [res_id], 'active_model': context.get("thread_model", server.object_id.model)})
                            cr.commit()
                        if numMsgs < MAX_POP_MESSAGES:
                            break
                        pop_server.quit()
                        _logger.debug("Fetched %d email(s) on %s server %s; %d succeeded, %d failed.", numMsgs, server.type, server.name, (numMsgs - failed), failed)
                except Exception:
                    error_description += '- ' + str(e) + '\n'
                    _logger.exception("General failure when trying to fetch mail from %s server %s.", server.type, server.name)
                finally:
                    if pop_server:
                        pop_server.quit()
            server.write({'date': time.strftime(tools.DEFAULT_SERVER_DATETIME_FORMAT)})

            server_history_vals = {
                'fetchmail_server_id': server.id,
                'action': 'fetch',
                'result': 'error' if error_description else 'success',
                'error_description': error_description,
                'email_successed_count': count,
                'email_failed_count': failed,
                'datetime_start': datetime_start,
                'datetime_end': datetime.datetime.now()
            }
            server_history_obj = self.pool.get('fetchmail.server.history')
            server_history_obj.create(cr, uid, server_history_vals)

        return True

    def _get_folder_path(self, server, folder_name):
        if not folder_name or folder_name=='':
            return folder_name

        folder_path = ''
        folder_path_components = folder_name.split('/')
        if server.email_account == 'aruba':
            folder_path = '.'.join(['INBOX'] + folder_path_components)
        else:
            folder_path = '/'.join(folder_path_components)

        return folder_path



class fetchmail_server_history(orm.Model):
    _name = 'fetchmail.server.history'
    _order = 'id DESC'
    _columns = {
        'fetchmail_server_id': fields.many2one('fetchmail.server', 'Server', readonly=True),
        'action': fields.selection([('fetch', 'Fetch')], 'Azione', readonly=True),
        'result': fields.selection([('success', 'SUCCESS'), ('error', 'ERROR')], 'Risultato', readonly=True),
        'error_description': fields.text('Errori', readonly=True),
        'email_successed_count': fields.integer('Email Processate', readonly=True),
        'email_failed_count': fields.integer('Email in Errore', readonly=True),
        'datetime_start': fields.datetime('Inizio', readonly=True),
        'datetime_end': fields.datetime('Fine', readonly=True),
    }