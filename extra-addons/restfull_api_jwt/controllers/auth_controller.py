import json

from ..utils.route_end_point import RouteEndPoint
from ..utils.exceptions_unauthorized import UnauthorizedInvalidToken, UnauthorizedMissingAuthorizationHeader
from odoo import exceptions,_
import sys
from ..service.auth_service import IAuthService  
from odoo import http
from odoo.http import request
from ..utils.base_ok_response import BaseOkResponse
from ..utils.base_bad_response import BaseBadResponse
from ..utils.custom_exception import  ParamsErrorException 
from ..service.dependency_container import dependency_container 
import requests
from ..utils.methods_constants import create_tokenSiginApple


class AuthController(http.Controller):
    authService: IAuthService = None
    def __init__(self):
         self.authService = dependency_container.get_dependency(IAuthService)
    
    @http.route(RouteEndPoint.signUp, methods=['POST'], auth='public', csrf=False, cors='*')
    def signUp(self, **kwargs):
      print('signUp')
      try:  
           result = self.authService.signUp()
           return request.make_response(BaseOkResponse(message=_("success signUp"),data=result).toJSON(), headers=[('Content-Type', 'application/json')], cookies=None, status=200)
      except json.decoder.JSONDecodeError as error:    
            return request.make_response(BaseBadResponse(message=_("invalid json data"),erorr= sys.exc_info()).toJSON(), headers=[('Content-Type', 'application/json')], cookies=None, status=400)
      except ParamsErrorException as error:
            return request.make_response(BaseBadResponse(message=error,erorr= sys.exc_info()).toJSON(), headers=[('Content-Type', 'application/json')], cookies=None, status=400)
      except exceptions.AccessDenied as error:
            return request.make_response(BaseBadResponse(message=_('password erorr'),erorr= sys.exc_info()).toJSON(), headers=[('Content-Type', 'application/json')], cookies=None, status=400)
      except exceptions.ValidationError as e:
            request.env.context = dict(request.env.context, erorr_exception = BaseBadResponse(message=e,erorr= sys.exc_info()[0]).toJSON(),statusCode= 400)
            pass
      except:
            request.env.context = dict(request.env.context, erorr_exception = BaseBadResponse(message=_("unexpected error"),erorr= sys.exc_info()[0]).toJSON(),statusCode= 400)
            return request.make_response(BaseBadResponse(message=_("unexpected error"),erorr= sys.exc_info()).toJSON(), headers=[('Content-Type', 'application/json')], cookies=None, status=400)
     
    @http.route(RouteEndPoint.signIn, methods=['POST'], auth='public', csrf=False, cors='*')
    def signIn(self, **kwargs):
      print('signIn')
      try: 
           result = self.authService.signIn()
           return request.make_response(BaseOkResponse(message=_("success login"),data=result).toJSON(), headers=[('Content-Type', 'application/json')], cookies=None, status=200)
      except json.decoder.JSONDecodeError as error:    
            return request.make_response(BaseBadResponse(message=_("invalid json data"),erorr= sys.exc_info()).toJSON(), headers=[('Content-Type', 'application/json')], cookies=None, status=400)
      except ParamsErrorException as error:
            return request.make_response(BaseBadResponse(message=error,erorr= sys.exc_info()).toJSON(), headers=[('Content-Type', 'application/json')], cookies=None, status=400)
      except exceptions.AccessDenied as error:
            return request.make_response(BaseBadResponse(message=_('password erorr'),erorr= sys.exc_info()).toJSON(), headers=[('Content-Type', 'application/json')], cookies=None, status=400)
      except exceptions.ValidationError as e:
            request.env.context = dict(request.env.context, erorr_exception = BaseBadResponse(message=e,erorr= sys.exc_info()[0]).toJSON(),statusCode= 400)
            pass
      except:
            request.env.context = dict(request.env.context, erorr_exception = BaseBadResponse(message=_("unexpected error"),erorr= sys.exc_info()[0]).toJSON(),statusCode= 400)
            return request.make_response(BaseBadResponse(message=_("unexpected error"),erorr= sys.exc_info()).toJSON(), headers=[('Content-Type', 'application/json')], cookies=None, status=400)
     
    @http.route(RouteEndPoint.logout, methods=['POST'], auth='jwt_portal_auth', csrf=False, cors='*')
    def logout(self, **kwargs):
      print('logout')
      try: 
           self.authService.validatorToken()
           self.authService.logout()
           return request.make_response(BaseOkResponse(message=_("success_logout"),data=None).toJSON(), headers=[('Content-Type', 'application/json')], cookies=None, status=200)  
      except UnauthorizedInvalidToken:    
            return request.make_response(BaseBadResponse(message=_("invalid token"),erorr= sys.exc_info(),statusCode=401).toJSON(), headers=[('Content-Type', 'application/json')], cookies=None, status=401)
      except UnauthorizedMissingAuthorizationHeader:    
            return request.make_response(BaseBadResponse(message=_("token missing"),erorr= sys.exc_info(),statusCode=401).toJSON(), headers=[('Content-Type', 'application/json')], cookies=None, status=401)
      except:
            request.env.context = dict(request.env.context, erorr_exception = BaseBadResponse(message=_("unexpected error"),erorr= sys.exc_info()[0]).toJSON(),statusCode= 400)
            return request.make_response(BaseBadResponse(message=_("unexpected error"),erorr= sys.exc_info()).toJSON(), headers=[('Content-Type', 'application/json')], cookies=None, status=400)
    
    
    @http.route(RouteEndPoint.logoutAllDevice, methods=['POST'], auth='jwt_portal_auth', csrf=False, cors='*')
    def logoutAllDevice(self, **kwargs):
      print('logoutAllDevice')
      try: 
           self.authService.validatorToken()
           self.authService.logoutAllDevice()
           return request.make_response(BaseOkResponse(message=_("success_logout_all_device"),data=None).toJSON(), headers=[('Content-Type', 'application/json')], cookies=None, status=200)  
      except UnauthorizedInvalidToken:    
            return request.make_response(BaseBadResponse(message=_("invalid token"),erorr= sys.exc_info(),statusCode=401).toJSON(), headers=[('Content-Type', 'application/json')], cookies=None, status=401)
      except UnauthorizedMissingAuthorizationHeader:    
            return request.make_response(BaseBadResponse(message=_("token missing"),erorr= sys.exc_info(),statusCode=401).toJSON(), headers=[('Content-Type', 'application/json')], cookies=None, status=401)
      except:
            request.env.context = dict(request.env.context, erorr_exception = BaseBadResponse(message=_("unexpected error"),erorr= sys.exc_info()[0]).toJSON(),statusCode= 400)
            return request.make_response(BaseBadResponse(message=_("unexpected error"),erorr= sys.exc_info()).toJSON(), headers=[('Content-Type', 'application/json')], cookies=None, status=400)
    
    @http.route(RouteEndPoint.refreshToken, methods=['POST'], auth='jwt_refresh_auth', csrf=False, cors='*')
    def refreshToken(self, **kwargs):
      print('logout')
      try: 
           self.authService.validatorRefreshToken()
           result = self.authService.refreshToken()
           return request.make_response(BaseOkResponse(message="ok",data=result).toJSON(), headers=[('Content-Type', 'application/json')], cookies=None, status=200)  
      except UnauthorizedInvalidToken:    
            return request.make_response(BaseBadResponse(message=_("invalid token"),erorr= sys.exc_info(),statusCode=401).toJSON(), headers=[('Content-Type', 'application/json')], cookies=None, status=401)
      except UnauthorizedMissingAuthorizationHeader:    
            return request.make_response(BaseBadResponse(message=_("token missing"),erorr= sys.exc_info(),statusCode=401).toJSON(), headers=[('Content-Type', 'application/json')], cookies=None, status=401)
      except:
            request.env.context = dict(request.env.context, erorr_exception = BaseBadResponse(message=_("unexpected error"),erorr= sys.exc_info()[0]).toJSON(),statusCode= 400)
            return request.make_response(BaseBadResponse(message=_("unexpected error"),erorr= sys.exc_info()).toJSON(), headers=[('Content-Type', 'application/json')], cookies=None, status=400)
    
    
    @http.route(RouteEndPoint.sendCode, methods=['POST'], auth='public', csrf=False, cors='*')
    def sendCode(self, **kwargs):
      print('sendCode')
      try:
        result = self.authService.sendCode() 
        return request.make_response(BaseOkResponse(message=_("the_code_has_send"),data=result).toJSON(), headers=[('Content-Type', 'application/json')], cookies=None, status=200)
      except json.decoder.JSONDecodeError as error:    
            return request.make_response(BaseBadResponse(message=_("invalid json data"),erorr= error).toJSON(), headers=[('Content-Type', 'application/json')], cookies=None, status=400)
      except ParamsErrorException as error:
            print(error)   
            return request.make_response(BaseBadResponse(message=error,erorr= sys.exc_info()).toJSON(), headers=[('Content-Type', 'application/json')], cookies=None, status=400)
      except exceptions.ValidationError as e:
            request.env.context = dict(request.env.context, erorr_exception = BaseBadResponse(message=e,erorr= sys.exc_info()[0]).toJSON(),statusCode= 400)
            pass
      except:
            request.env.context = dict(request.env.context, erorr_exception = BaseBadResponse(message=_("unexpected error"),erorr= sys.exc_info()[0]).toJSON(),statusCode= 400)
            return request.make_response(BaseBadResponse(message=_("unexpected error"),erorr= sys.exc_info()).toJSON(), headers=[('Content-Type', 'application/json')], cookies=None, status=400)
    
    
    @http.route(RouteEndPoint.registerConfirmCode, methods=['POST'], auth='jwt_confirm_auth', csrf=False, cors='*')
    def confirmCode(self, **kwargs):
      print('confirmCode')
      try:
        self.authService.validatorConfirmToken()
        result = self.authService.confirmCode() 
        return request.make_response(BaseOkResponse(message="ok",data=result).toJSON(), headers=[('Content-Type', 'application/json')], cookies=None, status=200)
      except json.decoder.JSONDecodeError as error:    
            return request.make_response(BaseBadResponse(message=_("invalid json data"),erorr= error).toJSON(), headers=[('Content-Type', 'application/json')], cookies=None, status=400)
      except UnauthorizedInvalidToken:    
            return request.make_response(BaseBadResponse(message=_("invalid token"),erorr= sys.exc_info(),statusCode=401).toJSON(), headers=[('Content-Type', 'application/json')], cookies=None, status=401)
      except UnauthorizedMissingAuthorizationHeader:    
            return request.make_response(BaseBadResponse(message=_("token missing"),erorr= sys.exc_info(),statusCode=401).toJSON(), headers=[('Content-Type', 'application/json')], cookies=None, status=401)
      except ParamsErrorException as error:
            print(error)   
            return request.make_response(BaseBadResponse(message=error,erorr= sys.exc_info()).toJSON(), headers=[('Content-Type', 'application/json')], cookies=None, status=400)
      except exceptions.ValidationError as e:
            request.env.context = dict(request.env.context, erorr_exception = BaseBadResponse(message=e,erorr= sys.exc_info()[0]).toJSON(),statusCode= 400)
            pass
      except:
            request.env.context = dict(request.env.context, erorr_exception = BaseBadResponse(message=_("unexpected error"),erorr= sys.exc_info()[0]).toJSON(),statusCode= 400)
            return request.make_response(BaseBadResponse(message=_("unexpected error"),erorr= sys.exc_info()).toJSON(), headers=[('Content-Type', 'application/json')], cookies=None, status=400)
   
   
    @http.route(RouteEndPoint.confirmResetPassword, methods=['POST'], auth='jwt_confirm_auth', csrf=False, cors='*')
    def confirmResetPassword(self, **kwargs):
      print('confirmCode')
      try:
        self.authService.validatorConfirmToken()
        result = self.authService.confirmResetPassword() 
        return request.make_response(BaseOkResponse(message="ok",data=result).toJSON(), headers=[('Content-Type', 'application/json')], cookies=None, status=200)
      except json.decoder.JSONDecodeError as error:    
            return request.make_response(BaseBadResponse(message=_("invalid json data"),erorr= error).toJSON(), headers=[('Content-Type', 'application/json')], cookies=None, status=400)
      except UnauthorizedInvalidToken:    
            return request.make_response(BaseBadResponse(message=_("invalid token"),erorr= sys.exc_info(),statusCode=401).toJSON(), headers=[('Content-Type', 'application/json')], cookies=None, status=401)
      except UnauthorizedMissingAuthorizationHeader:    
            return request.make_response(BaseBadResponse(message=_("token missing"),erorr= sys.exc_info(),statusCode=401).toJSON(), headers=[('Content-Type', 'application/json')], cookies=None, status=401)
      except ParamsErrorException as error:
            print(error)   
            return request.make_response(BaseBadResponse(message=error,erorr= sys.exc_info()).toJSON(), headers=[('Content-Type', 'application/json')], cookies=None, status=400)
      except exceptions.ValidationError as e:
            request.env.context = dict(request.env.context, erorr_exception = BaseBadResponse(message=e,erorr= sys.exc_info()[0]).toJSON(),statusCode= 400)
            pass
      except:
            request.env.context = dict(request.env.context, erorr_exception = BaseBadResponse(message=_("unexpected error"),erorr= sys.exc_info()[0]).toJSON(),statusCode= 400)
            return request.make_response(BaseBadResponse(message=_("unexpected error"),erorr= sys.exc_info()).toJSON(), headers=[('Content-Type', 'application/json')], cookies=None, status=400)

 
    @http.route(RouteEndPoint.changePassword, methods=['POST'], auth='jwt_reset_auth', csrf=False, cors='*')
    def changePassword(self, **kwargs):
      print('changePassword')
      try:
        self.authService.validatorResetToken()
        result = self.authService.changePassword() 
        return request.make_response(BaseOkResponse(message="ok",data=result).toJSON(), headers=[('Content-Type', 'application/json')], cookies=None, status=200)
      except json.decoder.JSONDecodeError as error:    
            return request.make_response(BaseBadResponse(message=_("invalid json data"),erorr= sys.exc_info()).toJSON(), headers=[('Content-Type', 'application/json')], cookies=None, status=400)
      except UnauthorizedInvalidToken:    
            return request.make_response(BaseBadResponse(message=_("invalid token"),erorr= sys.exc_info(),statusCode=401).toJSON(), headers=[('Content-Type', 'application/json')], cookies=None, status=401)
      except UnauthorizedMissingAuthorizationHeader:    
            return request.make_response(BaseBadResponse(message=_("token missing"),erorr= sys.exc_info(),statusCode=401).toJSON(), headers=[('Content-Type', 'application/json')], cookies=None, status=401)
      except ParamsErrorException as error:
            print(error)   
            return request.make_response(BaseBadResponse(message=error,erorr= sys.exc_info()).toJSON(), headers=[('Content-Type', 'application/json')], cookies=None, status=400)
      except exceptions.ValidationError as e:
            request.env.context = dict(request.env.context, erorr_exception = BaseBadResponse(message=e,erorr= sys.exc_info()[0]).toJSON(),statusCode= 400)
            pass
      except:
            request.env.context = dict(request.env.context, erorr_exception = BaseBadResponse(message=_("unexpected error"),erorr= sys.exc_info()[0]).toJSON(),statusCode= 400)
            return request.make_response(BaseBadResponse(message=_("unexpected error"),erorr= sys.exc_info()).toJSON(), headers=[('Content-Type', 'application/json')], cookies=None, status=400)

 
#     @http.route('/SiginApple', methods=['POST'], auth='public', csrf=False, cors='*')
#     def SiginApple(self, **kwargs):
#       print('changePassword')
#       try:
#         args =  request.get_json_data()
#         authorization_code = None
#         if('authorization_code' in args):
#              authorization_code = str(args.get('authorization_code'))
#         # Request payload
#         token = create_tokenSiginApple()
#         print(authorization_code)
#         print(token)
#         payload = {
#             'client_id': 'Roqay.com.QuranShaby',
#             'client_secret': token,
#             'code': authorization_code,
#             'grant_type': 'authorization_code',
#         }
#         # Send POST request
#         response = requests.post('https://appleid.apple.com/auth/token', data = payload )
        
#         # Check response status code
#         if response.status_code == 200:
#             # Successful request
#             # save access_token and refresh_token on database from response
#             print('Token request successful!')
#             print('Response:', response.json())
#         else:
#             # Request failed
#             print('Token request failed.')
#             print('Response status code:', response.status_code)
#             print('Response:', response.text)
#         return request.make_response(BaseOkResponse(message="ok",data=response.json()).toJSON(), headers=[('Content-Type', 'application/json')], cookies=None, status=200)
#       except json.decoder.JSONDecodeError as error:    
#             return request.make_response(BaseBadResponse(message=_("invalid json data"),erorr= sys.exc_info()).toJSON(), headers=[('Content-Type', 'application/json')], cookies=None, status=400)
#       except UnauthorizedInvalidToken:    
#             return request.make_response(BaseBadResponse(message=_("invalid token"),erorr= sys.exc_info(),statusCode=401).toJSON(), headers=[('Content-Type', 'application/json')], cookies=None, status=401)
#       except UnauthorizedMissingAuthorizationHeader:    
#             return request.make_response(BaseBadResponse(message=_("token missing"),erorr= sys.exc_info(),statusCode=401).toJSON(), headers=[('Content-Type', 'application/json')], cookies=None, status=401)
#       except ParamsErrorException as error:
#             print(error)   
#             return request.make_response(BaseBadResponse(message=error,erorr= sys.exc_info()).toJSON(), headers=[('Content-Type', 'application/json')], cookies=None, status=400)
#       except exceptions.ValidationError as e:
#             request.env.context = dict(request.env.context, erorr_exception = BaseBadResponse(message=e,erorr= sys.exc_info()[0]).toJSON(),statusCode= 400)
#             pass
#       except:
#             request.env.context = dict(request.env.context, erorr_exception = BaseBadResponse(message=_("unexpected error"),erorr= sys.exc_info()[0]).toJSON(),statusCode= 400)
#             return request.make_response(BaseBadResponse(message=_("unexpected error"),erorr= sys.exc_info()).toJSON(), headers=[('Content-Type', 'application/json')], cookies=None, status=400)

 