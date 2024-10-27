from flask import jsonify

class ResponseHandler:
    @staticmethod
    def success(message, data=None):
        response = {
            "success": True,
            "message": message
        }
        if data is not None:
            response["data"] = data
        return response
    
    @staticmethod
    def error(message):
        response = {
            "success": False,
            "error": message
        }
        return response