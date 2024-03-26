
# from pyparsing import 
from pyparsing import ParseException


class InvalidJSONDataException(Exception):
    def __init__(self, message): 
        super().__init__(message)     
   
class ParamsErrorException(Exception):
    #    message: Any
       message: ParseException