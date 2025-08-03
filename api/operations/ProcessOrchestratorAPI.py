from flask import Blueprint, jsonify, request
import requests
from logs.logger import get_logger
import time

logger = get_logger(__name__)

# Create a Blueprint for process orchestrator endpoints
process_orchestrator_bp = Blueprint('process_orchestrator', __name__)

@process_orchestrator_bp.route('/api/orchestrator/run-full-analysis', methods=['POST', 'OPTIONS'])
def runFullAnalysis():
    """API endpoint to sequentially run all three analysis processes"""
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Accept')
        return response, 200
        
    try:
        # Get optional parameters from request
        data = request.get_json() or {}
        min_holding = data.get('min_holding', '5000')
        
        logger.info("Starting full analysis orchestration")
        
        # Base URL for API calls (assuming localhost:8080)
        base_url = "http://localhost:8080"
        
        results = {
            'step1': None,
            'step2': None, 
            'step3': None,
            'errors': []
        }
        
        # Step 1: Update portfolio summary to get all tokens held by smart money
        logger.info("Step 1: Updating portfolio summary")
        try:
            step1_response = requests.post(
                f"{base_url}/api/portsummary/update",
                headers={'Content-Type': 'application/json'},
                timeout=300  # 5 minutes timeout
            )
            
            if step1_response.status_code == 200:
                results['step1'] = step1_response.json()
                logger.info("Step 1 completed successfully")
            else:
                error_msg = f"Step 1 failed with status {step1_response.status_code}: {step1_response.text}"
                logger.error(error_msg)
                results['errors'].append(error_msg)
                return create_error_response("Step 1 (portfolio update) failed", results)
                
        except requests.RequestException as e:
            error_msg = f"Step 1 request failed: {str(e)}"
            logger.error(error_msg)
            results['errors'].append(error_msg)
            return create_error_response("Step 1 (portfolio update) request failed", results)
        
        # Step 2: Get all wallets invested in tokens
        logger.info("Step 2: Getting wallets invested in all tokens")
        try:
            step2_response = requests.post(
                f"{base_url}/api/walletsinvested/persist/all",
                headers={'Content-Type': 'application/json'},
                timeout=600  # 10 minutes timeout
            )
            
            if step2_response.status_code == 200:
                results['step2'] = step2_response.json()
                logger.info("Step 2 completed successfully")
            else:
                error_msg = f"Step 2 failed with status {step2_response.status_code}: {step2_response.text}"
                logger.error(error_msg)
                results['errors'].append(error_msg)
                return create_error_response("Step 2 (wallets invested) failed", results)
                
        except requests.RequestException as e:
            error_msg = f"Step 2 request failed: {str(e)}"
            logger.error(error_msg)
            results['errors'].append(error_msg)
            return create_error_response("Step 2 (wallets invested) request failed", results)
        
        # Step 3: Get investment details for all wallets above certain holdings
        logger.info(f"Step 3: Getting investment details for wallets with min holding {min_holding}")
        try:
            step3_response = requests.post(
                f"{base_url}/api/walletinvestement/investmentdetails/all",
                headers={'Content-Type': 'application/json'},
                json={'min_holding': min_holding},
                timeout=900  # 15 minutes timeout
            )
            
            if step3_response.status_code == 200:
                results['step3'] = step3_response.json()
                logger.info("Step 3 completed successfully")
            else:
                error_msg = f"Step 3 failed with status {step3_response.status_code}: {step3_response.text}"
                logger.error(error_msg)
                results['errors'].append(error_msg)
                return create_error_response("Step 3 (investment details) failed", results)
                
        except requests.RequestException as e:
            error_msg = f"Step 3 request failed: {str(e)}"
            logger.error(error_msg)
            results['errors'].append(error_msg)
            return create_error_response("Step 3 (investment details) request failed", results)
        
        # All steps completed successfully
        logger.info("Full analysis orchestration completed successfully")
        
        response = jsonify({
            'success': True,
            'message': 'Full analysis completed successfully',
            'results': results,
            'execution_summary': {
                'step1_status': 'completed',
                'step2_status': 'completed', 
                'step3_status': 'completed',
                'min_holding_used': min_holding
            }
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
        
    except Exception as e:
        logger.error(f"Orchestrator error: {str(e)}")
        response = jsonify({
            'success': False,
            'message': f'Orchestrator internal error: {str(e)}',
            'results': results
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

def create_error_response(message, results):
    """Helper function to create error responses with CORS headers"""
    response = jsonify({
        'success': False,
        'message': message,
        'results': results
    })
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response, 500