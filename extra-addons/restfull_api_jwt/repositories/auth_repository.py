from werkzeug.exceptions import Forbidden, Unauthorized
from ..service.auth_service import IAuthService
from ..utils.exceptions_unauthorized import UnauthorizedInvalidToken
from ..utils.response_models.user_auth_response import UserAuthResponce
from odoo.http import request
from ..utils.custom_exception import ParamsErrorException
import jwt
from ..utils.methods_constants import check_data, check_and_remove_country_code_of_saudi_arabia, fetchRequestLanguage, getValidatorConfirmAuth, getValidatorPortalAuth, accessTokenExpiresIn, getValidatorRefreshAuth, getValidatorResetAuth, refreshTokenExpiresIn, confirmResetExpiresIn, create_token
from ..utils.models_name import ModelsName
from odoo.addons.auth_jwt_jks.key_manager import KeyManager
from odoo.addons.auth_jwt.models.ir_http import IrHttpJwt


import logging
_logger = logging.getLogger(__name__)


class AuthRepository(IAuthService):

    def __init__(self):
        # Initialize KeyManager
        self.key_manager = KeyManager()  # This will ensure keys are loaded
        self.public_key = self.key_manager.get_public_key()
        self.private_key = self.key_manager.get_private_key()

    def signUp(self):
        fetchRequestLanguage()
        args = request.get_json_data()
        # TO-Check we might need to add email to required field
        required_fields = ['name', 'country_id', 'mobile', 'password']
        if not any(field not in args.keys() for field in required_fields):
            login = str(args.get('mobile'))
            phone_number = check_and_remove_country_code_of_saudi_arabia(login)
            password = str(args.get('password'))
            name = str(args.get('name'))

            _logger.debug("Processing signup with login data: %s", {
                'name': name,
                'login': phone_number,
                'password': 'FILTERED',
                'mobile': login
            })
            # Create a user
            user_sudo = request.env[ModelsName.usersRES].sudo().create({
                'name': name,
                'login': phone_number,
                'password': password,
            })
            # add user detiles
            user_sudo.partner_id.sudo().write({
                'name': name,
                'email': str(args.get('email', None)),
                'country_id': str(args.get('country_id')),
                'mobile': phone_number

            })

            user_sudo.sudo().random_confirmation_code()
            print("confirmation_code :", user_sudo.confirmation_code)
            validatorConfirmAuth = getValidatorConfirmAuth()
            confirmToken = create_token(
                validatorConfirmAuth, expiresIn=refreshTokenExpiresIn, partner_id=user_sudo.partner_id.id, secret=self.private_key)
            return {"confirm_token": confirmToken}
        else:
            raise ParamsErrorException(
                "the fields name,mobile,country_id or password are not found in json body")

    def signIn(self):
        fetchRequestLanguage()
        validatorPortalAuth = getValidatorPortalAuth()
        validatorRefreshAuth = getValidatorRefreshAuth()
        args = request.get_json_data()
        if 'login' in args and 'password' in args:
            login = str(args.get('login'))
            phone_number = check_and_remove_country_code_of_saudi_arabia(login)
            password = str(args.get('password'))
            user_sudo = None
            # get user

            if phone_number != None:
                user_sudo = request.env[ModelsName.usersRES].sudo().search(
                    [('login', '=', phone_number)], limit=1)
            else:
                user_sudo = request.env[ModelsName.usersRES].sudo().search(
                    [('name', '=', phone_number)], limit=1)

            # check user
            _logger.debug("Processing signin with login data befor usersudo: %s", {
                'user_sudo': user_sudo,

            })
            if user_sudo:
                user_sudo.check(request.session.db,
                                uid=user_sudo.id, passwd=password)
                accessToken = create_token(
                    validatorPortalAuth, expiresIn=accessTokenExpiresIn, partner_id=user_sudo.partner_id.id, secret=self.private_key)
                refreshToken = create_token(
                    validatorRefreshAuth, expiresIn=refreshTokenExpiresIn, partner_id=user_sudo.partner_id.id, secret=self.private_key)
                _logger.debug("Processing signin with login data: %s", {
                    'user_sudo': user_sudo,

                })
                user_responce = UserAuthResponce(
                    id=user_sudo.id,
                    name=check_data(user_sudo.name),
                    email=check_data(user_sudo.email),
                    company_id=user_sudo.company_id.id,
                    company_name=check_data(user_sudo.company_id.name),
                    access_token=accessToken,
                    refresh_token=refreshToken,
                    is_complete=user_sudo.is_complete
                )
                _logger.debug("Processing signin with login data: %s", {
                    'user_responce': user_responce,

                })
                return vars(user_responce)
            else:
                raise ParamsErrorException("user_not_found")
        else:
            raise ParamsErrorException(
                "the key login or password are not found in json bady")

    def logout(self):
        request.session.logout(keep_db=True)

    def logoutAllDevice(self):
        fetchRequestLanguage()
        user_sudo = request.env[ModelsName.usersRES].sudo().search(
            [('partner_id', '=', request.jwt_partner_id)], limit=1)
        user_tokens = request.env[ModelsName.authUsersTokens].sudo().search(
            [('user_id', '=', user_sudo.id)])
        print(user_tokens)
        if user_tokens:
            user_tokens.mapped(lambda user_token: user_token.revoked_token())
        pass

    def sendCode(self):
        fetchRequestLanguage()
        args = request.get_json_data()
        if 'number' in args:
            phone_number = check_and_remove_country_code_of_saudi_arabia(
                str(args.get('number')))
            if phone_number == None:
                raise ParamsErrorException("the number is incorrect")
            # number correct
            user_sudo = request.env[ModelsName.usersRES].sudo().search(
                [('login', '=', phone_number)], limit=1)
            if user_sudo:
                user_sudo.sudo().random_confirmation_code()
                # add Service confirmation_code
                print("confirmation_code :", user_sudo.confirmation_code)
                _logger.debug("confirmation_code : %s", {
                              user_sudo.confirmation_code})
                validatorConfirmAuth = getValidatorConfirmAuth()
                confirmToken = create_token(
                    validatorConfirmAuth, expiresIn=refreshTokenExpiresIn, partner_id=user_sudo.partner_id.id, secret=self.private_key)
                return {"confirm_token": confirmToken}
            else:
                raise ParamsErrorException("the number is not found")
        else:
            raise ParamsErrorException("the key number is not found json")

    def refreshToken(self):
        fetchRequestLanguage()
        if self.validatorRefreshToken():
            user_sudo = request.env[ModelsName.usersRES].sudo().search(
                [('partner_id', '=', request.jwt_partner_id)], limit=1)
            validatorPortalAuth = getValidatorPortalAuth()
            accessToken = create_token(
                validatorPortalAuth, expiresIn=accessTokenExpiresIn, partner_id=user_sudo.partner_id.id, secret=self.private_key)
            return {"access_token": accessToken}

    def confirmResetPassword(self):
        fetchRequestLanguage()
        if self.validatorConfirmToken():
            args = request.get_json_data()
            if 'confirmation_code' in args:
                confirmation_code = int(args.get('confirmation_code'))
                user_sudo = request.env[ModelsName.usersRES].sudo().search(
                    [('partner_id', '=', request.jwt_partner_id)], limit=1)
                if user_sudo:
                    if user_sudo.confirmation_code == confirmation_code:
                        validatorResetAuth = getValidatorResetAuth()
                        confirmResetToken = create_token(
                            validatorResetAuth, expiresIn=confirmResetExpiresIn, partner_id=user_sudo.partner_id.id, secret=self.private_key)
                    else:
                        raise ParamsErrorException(
                            "confirmation code is not equal")
                else:
                    raise ParamsErrorException("user_not_found")

                return {"confirm_reset_token": confirmResetToken}
            else:
                raise ParamsErrorException(
                    "the key confirmation code isnot found in json bady")

    def confirmCode(self):
        fetchRequestLanguage()
        if self.validatorRefreshToken():
            args = request.get_json_data()
            if 'confirmation_code' in args:
                confirmation_code = int(args.get('confirmation_code'))
                user_sudo = request.env[ModelsName.usersRES].sudo().search(
                    [('partner_id', '=', request.jwt_partner_id)], limit=1)
                if user_sudo:
                    if not user_sudo.is_complete:
                        if user_sudo.confirmation_code == confirmation_code:
                            user_sudo.sudo().write({
                                "active": True,
                                "is_complete": True
                            })
                            # get validator Tokens
                            validatorPortalAuth = getValidatorPortalAuth()
                            validatorRefreshAuth = getValidatorRefreshAuth()
                            # create Tokens and save in UsersTokens
                            accessToken = create_token(
                                validatorPortalAuth, expiresIn=accessTokenExpiresIn, partner_id=user_sudo.partner_id.id, secret=self.private_key)
                            refreshToken = create_token(
                                validatorRefreshAuth, expiresIn=refreshTokenExpiresIn, partner_id=user_sudo.partner_id.id, secret=self.private_key)
                            user_responce = UserAuthResponce(
                                id=user_sudo.id,
                                name=check_data(user_sudo.name),
                                email=check_data(user_sudo.email),
                                company_id=user_sudo.company_id.id,
                                company_name=check_data(user_sudo.company_id.name),
                                access_token=accessToken,
                                refresh_token=refreshToken,
                                is_complete=user_sudo.is_complete
                            )
                            return vars(user_responce)
                        else:
                            raise ParamsErrorException(
                                "confirmation code is not equal")
                    else:
                        raise ParamsErrorException("the user is completed")
                else:
                    raise ParamsErrorException("user_not_found")
            else:
                raise ParamsErrorException(
                    "the key confirmation code is not found in json bady")

    def changePassword(self):
        # if the user is athenticated and old password is no provided
        fetchRequestLanguage()
        if self.validatorResetToken():
            args = request.get_json_data()
            if 'new_password' in args:
                # new_password = int(args.get('new_password'))
                new_password = args.get('new_password')
                user_sudo = request.env[ModelsName.usersRES].sudo().search(
                    [('partner_id', '=', request.jwt_partner_id)], limit=1)
                if user_sudo:
                    # user_sudo.change_password(password=new_password)
                    user_sudo._change_password(new_password)
                    return 'ok'
                else:
                    raise ParamsErrorException("user not found")
            else:
                raise ParamsErrorException(
                    "the key new password is not found in json bady")

    def validatorToken(self):
        try:
            token = request.env["ir.http"]._get_bearer_token()
            decoded_token = jwt.decode(token, self.public_key, algorithms=["RS256"])
            self._validate_token_expiry(decoded_token)
            return True

        except jwt.ExpiredSignatureError:
            raise UnauthorizedInvalidToken
        except jwt.InvalidTokenError:
            raise Forbidden

    def validatorRefreshToken(self):
        fetchRequestLanguage()
        try:
            IrHttpJwt._get_jwt_payload(getValidatorRefreshAuth())
            return True
        except jwt.ExpiredSignatureError:
            raise UnauthorizedInvalidToken
        except jwt.InvalidTokenError:
            raise Forbidden

    def validatorConfirmToken(self):
        fetchRequestLanguage()
        try:
            IrHttpJwt._get_jwt_payload(getValidatorConfirmAuth())
            return True
        except jwt.ExpiredSignatureError:
            raise UnauthorizedInvalidToken
        except jwt.InvalidTokenError:
            raise Forbidden

    def validatorResetToken(self):
        fetchRequestLanguage()
        try:
            IrHttpJwt._get_jwt_payload(getValidatorResetAuth())
            return True
        except jwt.ExpiredSignatureError:
            raise UnauthorizedInvalidToken
        except jwt.InvalidTokenError:
            raise Forbidden

    def _get_bearer_token(self):
        return request.env["ir.http"]._get_bearer_token()
