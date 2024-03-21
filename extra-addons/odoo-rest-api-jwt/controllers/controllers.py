# -*- coding: utf-8 -*-
import json
import math
import logging
import requests
import sys
from functools import wraps

from odoo import http, _, exceptions
from odoo.http import request


from .serializers import Serializer
from .exceptions import QueryFormatError

from odoo.addons.restfull_api_jwt.service.auth_service import IAuthService
from odoo.addons.restfull_api_jwt.service.dependency_container import dependency_container

from odoo.addons.restfull_api_jwt.utils.exceptions_unauthorized import UnauthorizedInvalidToken, UnauthorizedMissingAuthorizationHeader
from odoo.addons.restfull_api_jwt.utils.custom_exception import ParamsErrorException


_logger = logging.getLogger(__name__)


def error_response(error, msg, status=400):
    """Generates error responses in a JSON-RPC-like format."""
    _logger.debug("error_response_data triggered")

    if isinstance(error, str):
        error_name = error
        error_args = [msg]
        exception_type = "CustomError"
    else:
        error_name = "NoneError" if error is None else str(
            error.__class__.__name__)
        error_args = [] if error is None else list(error.args)
        exception_type = "NoneType" if error is None else type(error).__name__

    response = {
        "jsonrpc": "2.0",
        "id": None,
        "error": {
            "code": status,
            "message": "Odoo Server Error",
            "data": {
                "name": error_name,
                "debug": "",
                "message": msg,
                "arguments": error_args,
                "exception_type": exception_type
            }
        }
    }
    return request.make_response(json.dumps(response), headers=[('Content-Type', 'application/json')], cookies=None, status=status)


class OdooAPI(http.Controller):
    _logger.debug("OdooAPI  Controller triggered")
    authService: IAuthService = None

    def __init__(self):
        self.authService = dependency_container.get_dependency(IAuthService)

    def process_put_data_fields(self, data):
        for field, value in data.items():
            if isinstance(value, dict):
                data[field] = self.process_put_nested_operations(value)
            elif isinstance(value, list):
                data[field] = [(6, _, value)]  # Replace operation
            else:
                # Handle simple fields or log as necessary
                _logger.debug(
                    "Processing simple field: %s with value %s", field, value)

    def process_put_nested_operations(self, field_data):
        operations = []
        for operation, ids in field_data.items():
            if operation == "push":
                operations += [(4, id, 0) for id in ids]
            elif operation == "pop":
                operations += [(3, id, 0) for id in ids]
            elif operation == "delete":
                operations += [(2, id, 0) for id in ids]
            else:
                _logger.warning("Unsupported operation: %s", operation)
        return operations

    @http.route(
        '/object/<string:model>/<string:function>',
        type='json', auth='user', methods=["POST"], csrf=False)
    def call_model_function(self, model, function, **post):
        args = []
        kwargs = {}
        if "args" in post:
            args = post["args"]
        if "kwargs" in post:
            kwargs = post["kwargs"]
        model = request.env[model]
        result = getattr(model, function)(*args, **kwargs)
        return result

    @http.route(
        '/object/<string:model>/<int:rec_id>/<string:function>',
        type='json', auth='user', methods=["POST"], csrf=False)
    def call_obj_function(self, model, rec_id, function, **post):
        args = []
        kwargs = {}
        if "args" in post:
            args = post["args"]
        if "kwargs" in post:
            kwargs = post["kwargs"]
        obj = request.env[model].browse(rec_id).ensure_one()
        result = getattr(obj, function)(*args, **kwargs)
        return result

    @http.route(
        '/api/<string:model>',
        type='http', auth='jwt_portal_auth', methods=['GET'], csrf=False)
    def get_model_data(self, model, **params):
        _logger.debug("get_model_data triggered")
        self.authService.validatorToken()

        try:
            records = request.env[model].search([])

        except KeyError as e:
            msg = "The model `%s` does not exist." % model

            # return request.make_response(BaseBadResponse(message=_(f"The model `{model}` does not exist."),erorr= sys.exc_info()).toJSON(), headers=[('Content-Type', 'application/json')], cookies=None, status=404)
            return error_response(e, msg, 404)

        try:
            if "query" in params:
                query = params["query"]
            else:
                query = "{*}"

            if "order" in params:
                orders = json.loads(params["order"])
            else:
                orders = "id ASC"

            if "filter" in params:
                filters = json.loads(params["filter"])
                records = request.env[model].search(filters, order=orders)

            prev_page = None
            next_page = None
            total_page_number = 1
            current_page = 1

            if "page_size" in params:
                page_size = int(params["page_size"])
                count = len(records)
                total_page_number = math.ceil(count/page_size)

                if "page" in params:
                    current_page = int(params["page"])
                else:
                    current_page = 1  # Default page Number
                start = page_size*(current_page-1)
                stop = current_page*page_size
                records = records[start:stop]
                next_page = current_page+1 \
                    if 0 < current_page + 1 <= total_page_number \
                    else None
                prev_page = current_page-1 \
                    if 0 < current_page - 1 <= total_page_number \
                    else None

            if "limit" in params:
                limit = int(params["limit"])
                records = records[0:limit]
            _logger.debug("get_model_data %s %s", records, query)

            try:
                serializer = Serializer(records, query, many=True)
                data = serializer.data
            except (SyntaxError, QueryFormatError) as e:
                # return request.make_response(BaseBadResponse(message=_(f"'{e.msg}"),erorr= sys.exc_info()).toJSON(), headers=[('Content-Type', 'application/json')], cookies=None, status=200)
                return error_response(e, _(f'{e.msg}'), 200)
            res = {
                "count": len(records),
                "prev": prev_page,
                "current": current_page,
                "next": next_page,
                "total_pages": total_page_number,
                "result": data
            }

            return request.make_response(json.dumps(res), headers=[('Content-Type', 'application/json')], status=200)

        except json.JSONDecodeError as e:
            return error_response(e, _("invalid json data"), status=400)
        except ParamsErrorException as error:
            # Assuming ParamsErrorException includes a message
            return error_response(error, str(error), status=400)
        except exceptions.AccessError as e:
            _logger.warning("Access to the record denied.", exc_info=True)
            # Changed to 403 to reflect access denial
            return error_response(e, _('Access denied.'), status=403)
        except Exception as e:
            _logger.error(
                "Unexpected error during data retrieval: %s", str(e), exc_info=True)
            return error_response(e, _('Unexpected error occurred.'), status=500)
    # This is for single record get

    @http.route(
        '/api/<string:model>/<int:rec_id>',
        type='http', auth='jwt_portal_auth', methods=['GET'], csrf=False)
    def get_model_rec(self, model, rec_id, **params):
        _logger.debug("get_model_rec triggered")
        self.authService.validatorToken()
        try:
            records = request.env[model].search([])
        except KeyError as e:
            msg = "The model `%s` does not exist." % model
            return error_response(e, msg, 404)

        try:
            if "query" in params:
                query = params["query"]
            else:
                query = "{*}"

            record = records.browse(rec_id).ensure_one()

            try:
                serializer = Serializer(record, query)
                data = serializer.data
            except (SyntaxError, QueryFormatError) as e:
                return error_response(e, _(f'{e.msg}'), 200)

            return request.make_response(json.dumps(data), headers=[('Content-Type', 'application/json')], status=200)

        except json.JSONDecodeError as e:
            return error_response(e, _("invalid json data"), status=400)
        except ValueError as e:
            _logger.warning("Expected a single record.", exc_info=True)
            return error_response(e, _('Expected a single record but got a different count.'), status=400)
        except ParamsErrorException as error:
            # Assuming ParamsErrorException includes a message
            return error_response(error, str(error), status=400)
        except Exception as e:
            _logger.error(
                "Unexpected error during data retrieval: %s", str(e), exc_info=True)
            return error_response(e, _('Unexpected error occurred.'), status=500)

    @http.route(
        '/api/<string:model>/',
        type='json', auth="jwt_portal_auth", methods=['POST'], csrf=False)
    def post_model_data(self, model, **post):
        self.authService.validatorToken()
        _logger.debug("post_model_data triggered for model: %s", model)
        # Extract and validate 'data' key from the params
        data = post.get('data', {})
        _logger.debug("post_model_data post['data']: %s", data)
        if not data:
            _logger.debug("post_model_data post['not data']: %s", data)
            message = ('`data` parameter is not found in POST request body.')
            raise exceptions.ValidationError(message)
        if not isinstance(data, dict):
            _logger.debug("post_model_data post['JSON']: %s", data)
            message = _('`data` parameter must be a JSON object.')
            raise exceptions.ValidationError(message)

        try:
            model_to_post = request.env[model]
        except KeyError as e:
            msg = "The model `%s` does not exist." % model
            raise exceptions.ValidationError(msg)
        # TODO: Handle data validation
        # Data validation logic goes here
        # For example, checking if required fields are present in data
        context = post.get('context', {})
        try:
            if context:
                # context = post.get("context")
                _logger.debug("post_model_data context: %s", context)

                record = model_to_post.with_context(**context).create(data)
            else:
                record = model_to_post.create(data)
            response = {"success": True, "id": record.id,
                        'message': "Record created successfully"}
            _logger.debug("post_model_data record: %s", record.id)
            return response
        except exceptions.ValidationError as e:
            _logger.warning("Expected a single record.", exc_info=True)
            msg = _(
                f"Validation error while creating record in model `{model}`")
            raise exceptions.ValidationError(msg)
        except ValueError as e:
            _logger.warning(str(e), exc_info=True)
            raise ValueError(str(e))
        except Exception as e:
            _logger.error("Failed to create data for model %s: %s",
                          model, str(e), exc_info=True)
            msg = _(f"Failed to create data for model `{model}`")
            raise Exception(msg)

    # This is for single record update
    @http.route(
        '/api/<string:model>/<int:rec_id>/',
        type='json', auth="jwt_portal_auth", methods=['PUT'], csrf=False)
    def put_model_record(self, model, rec_id, **post):
        self.authService.validatorToken()
        data = post.get('data', {})
        if not data:
            _logger.debug("put_model_record ['not data']: %s", data)
            message = ('`data` parameter is not found in PUT request body.')
            raise exceptions.ValidationError(message)

        if not isinstance(data, dict):
            _logger.debug("put_model_record post['JSON']: %s", data)
            message = _('`data` parameter must be a JSON object.')
            raise exceptions.ValidationError(message)

        try:
            model_to_put = request.env[model]
        except KeyError:
            msg = "The model `%s` does not exist." % model
            raise exceptions.ValidationError(msg)

        context = post.get('context', {})
        try:
            if context:
                rec = model_to_put.with_context(**post["context"])\
                    .browse(rec_id).ensure_one()
            else:
                rec = model_to_put.browse(rec_id).ensure_one()

        except ValueError as e:
            raise ValueError("Expected singleton: %s", str(e))

        self.process_put_data_fields(data)

        if rec.exists():
            try:
                rec.write(data)
                _logger.debug("data updated: %s", rec)
                return
            except Exception as e:
                _logger.error("Error during record update: %s",
                              e, exc_info=True)
                raise exceptions.ValidationError("Update failed: %s" % str(e))

        else:
            # No records to update
            _logger.debug("No records found matching the given id.")
            raise exceptions.ValidationError(
                "No records found matching the given id.")

    # This is for bulk update by filter

    @http.route(
        '/api/<string:model>/',
        type='json', auth="jwt_portal_auth", methods=['PUT'], csrf=False)
    def put_model_records(self, model, **post):
        self.authService.validatorToken()
        data = post.get('data', {})
        if not data:
            _logger.debug("put_model_record ['not data']: %s", data)
            message = ('`data` parameter is not found in PUT request body.')
            raise exceptions.ValidationError(message)

        if not isinstance(data, dict):
            _logger.debug("put_model_record post['JSON']: %s", data)
            message = _('`data` parameter must be a JSON object.')
            raise exceptions.ValidationError(message)

        try:
            model_to_put = request.env[model]
        except KeyError:
            msg = "The model `%s` does not exist." % model
            raise exceptions.ValidationError(msg)

        filters = post.get('filter')
        if not filters:
            raise exceptions.ValidationError(
                "`filter` parameter is required for PUT request.")

        context = post.get('context', {})
        try:
            if context:
                recs = model_to_put.with_context(**post["context"])\
                    .search(filters)
            else:
                recs = model_to_put.search(filters)

        except exceptions.ValidationError as e:
            _logger.debug("Validation error occurred %s", recs)
            raise exceptions.ValidationError(
                "Validation error occurred: %s", str(e))

        self.process_put_data_fields(data)

        if recs.exists():
            try:
                recs.write(data)
                _logger.debug("data updated: %s", recs)
                return
            except Exception as e:
                # return False
                _logger.error("Error during record update: %s",
                              e, exc_info=True)
                raise exceptions.ValidationError("Update failed: %s" % str(e))
        else:
            # No records to update
            _logger.debug("No records found matching the given filters.")
            raise exceptions.ValidationError(
                "No records found matching the given filters.")
            # return True

    # This is for deleting one record

    @http.route(
        '/api/<string:model>/<int:rec_id>/',
        type='http', auth="jwt_portal_auth", methods=['DELETE'], csrf=False)
    def delete_model_record(self, model,  rec_id, **post):
        self.authService.validatorToken()
        try:
            model_to_del_rec = request.env[model]

        except KeyError as e:
            msg = "The model `%s` does not exist." % model
            return error_response(e, msg, 404)

        rec = model_to_del_rec.search([('id', '=', rec_id)])
        _logger.debug("search: %s", rec)

        if not rec.exists():
            # No records to update
            _logger.debug("No records found matching the given id.")

            return error_response('RecordNotFoundError', _("Record does not exist or has been deleted."), status=404)

        try:
            is_deleted = rec.unlink()
            res = {
                "code": 200,
                "result": is_deleted
            }
            _logger.debug(
                "Successfully deleted: %s", rec)
            return request.make_response(json.dumps(res), headers=[('Content-Type', 'application/json')], status=200)

        except Exception as e:
            _logger.error(
                "Unexpected error during data retrieval: %s", str(e), exc_info=True)
            return error_response(e, _('Unexpected error occurred.'), status=500)

    # This is for bulk deletion

    @http.route(
        '/api/<string:model>/',
        type='http', auth="jwt_portal_auth", methods=['DELETE'], csrf=False)
    def delete_model_records(self, model, **post):
        self.authService.validatorToken()
        try:
            model_to_del_rec = request.env[model]

        except KeyError as e:
            msg = "The model `%s` does not exist." % model
            return error_response(e, msg, 404)

        filters = post.get("filter")
        if not filters:
            return error_response("MissingFilterError", "'filter' parameter is required.", 400)

        try:
            filters = json.loads(filters)
        except json.JSONDecodeError as e:
            return error_response(e, "Invalid JSON format for 'filter'.", 400)

        recs = model_to_del_rec.search(filters)

        if not recs:
            return error_response("RecordNotFoundError", "No records found matching the given filters.", 404)

        try:
            is_deleted = recs.unlink()
            res = {
                "code": 200,
                "result": is_deleted
            }
            _logger.debug(
                "Successfully deleted: %s", recs)
            return request.make_response(json.dumps(res), headers=[('Content-Type', 'application/json')], status=200)
        except Exception as e:
            _logger.error("Unexpected error during deletion: %s",
                          e, exc_info=True)
            return error_response(e, _('Unexpected error occurred.'), 500)

    @http.route(
        '/api/<string:model>/<int:rec_id>/<string:field>',
        type='http', auth="jwt_portal_auth", methods=['GET'], csrf=False)
    def get_binary_record(self, model,  rec_id, field, **post):
        self.authService.validatorToken()

        try:
            request.env[model]
        except KeyError as e:
            msg = "The model `%s` does not exist." % model
            return error_response(e, msg, 404)

        rec = request.env[model].browse(rec_id).ensure_one()
        if rec.exists():
            src = getattr(rec, field).decode("utf-8")
        else:
            src = False
        return http.Response(
            src
        )
