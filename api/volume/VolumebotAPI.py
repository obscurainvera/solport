from flask import jsonify, Blueprint, request
from scheduler.VolumebotScheduler import VolumeBotScheduler
from actions.VolumebotAction import VolumebotAction
from database.operations.sqlite_handler import SQLitePortfolioDB
from config.Security import COOKIE_MAP, isValidCookie
from logs.logger import get_logger

logger = get_logger(__name__)

volumebot_bp = Blueprint('volumebot', __name__)

@volumebot_bp.route('/api/volumebot/fetch-tokens-scheduled', methods=['POST', 'OPTIONS'])
def scheduleVolumeTokensFetch():
    """Execute the scheduler's execute_actions function for volume tokens"""
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Accept')
        return response, 200
        
    try:
        scheduler = VolumeBotScheduler()
        scheduler.handleVolumeAnalysisFromAPI()
        
        response = jsonify({
            'success': True,
            'message': 'Successfully triggered scheduled volume tokens fetch'
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response

    except Exception as e:
        logger.error(f"API Error in scheduleVolumeTokensFetch: {str(e)}")
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

# Add a new endpoint that matches the one used in the frontend
@volumebot_bp.route('/api/volumebot/fetch', methods=['POST', 'OPTIONS'])
def fetchVolumeTokens():
    """Alias for scheduleVolumeTokensFetch to match frontend endpoint"""
    return scheduleVolumeTokensFetch()

