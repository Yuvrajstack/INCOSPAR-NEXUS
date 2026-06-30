import json
import uuid
from datetime import datetime
from typing import Dict, List, Any
from sqlalchemy.orm import Session

from app.models.database_models import PredictionHistory, TelemetryHistory, Device
from app.services.predictive_models import LSTMPredictor, XGBoostClassifier, IsolationForestAnomalyDetector
from app.services.graph_analysis_engine import graph_analysis_engine
from app.services.explainability_engine import explainability_engine

class PredictiveEngineService:
    """
    SentinelNet AI Predictive Engine Service.
    Orchestrates models, graph analyses, explainability triggers, and SQL persistence.
    """

    def __init__(self):
        self.model_version = "SENTINEL-v3.0.0"
        
        # Model instances (following SOLID interface design)
        self.lstm = LSTMPredictor()
        self.xgboost = XGBoostClassifier()
        self.isolation_forest = IsolationForestAnomalyDetector()

        # In-memory prediction tracking caches
        self.latest_predictions: Dict[str, dict] = {}
        self.confidence_caches: Dict[str, List[float]] = {}
        self.trend_caches: Dict[str, str] = {}

    def get_predictions(self, db: Session) -> List[dict]:
        """Returns the cached list of active predictions for all devices."""
        # If cache is empty, populate it
        if not self.latest_predictions:
            self.run_predictions_pass(db)
        return list(self.latest_predictions.values())

    def get_prediction_history(self, db: Session, limit: int = 100) -> List[dict]:
        """Retrieves prediction history records from SQLite."""
        history = db.query(PredictionHistory).order_by(PredictionHistory.timestamp.desc()).limit(limit).all()
        result = []
        for h in history:
            result.append({
                "id": h.id,
                "prediction_id": h.prediction_id,
                "timestamp": h.timestamp.isoformat(),
                "created_at": h.created_at.isoformat(),
                "device_id": h.device_id,
                "model_version": h.model_version,
                "failure_probability": h.failure_probability,
                "confidence": h.confidence,
                "confidence_history": json.loads(h.confidence_history_json),
                "prediction_trend": h.prediction_trend,
                "prediction_status": h.prediction_status,
                "predicted_failure_type": h.predicted_failure_type,
                "root_cause_signals": json.loads(h.root_cause_signals_json),
                "contributing_metrics": json.loads(h.contributing_metrics_json),
                "recommended_action": h.recommended_action,
                "business_impact": json.loads(h.business_impact_json),
                "blast_radius": h.blast_radius,
                "mission_criticality": h.mission_criticality
            })
        return result

    def get_risk_profile(self, db: Session) -> Dict[str, Any]:
        """Generates the risk levels classification and overall network health scores."""
        preds = self.get_predictions(db)
        
        device_risks = {}
        healthy_count = 0
        warning_count = 0
        critical_count = 0
        
        total_health = 0.0
        
        for p in preds:
            dev_id = p["device_id"]
            risk = p["risk_level"]
            status = p["prediction_status"]
            prob = p["failure_probability"]
            
            device_health = max(0.0, 100.0 - (prob * 100.0))
            total_health += device_health
            
            device_risks[dev_id] = {
                "risk_level": risk,
                "prediction_status": status,
                "failure_probability": prob,
                "health_score": round(device_health, 2)
            }
            
            if status == "NORMAL":
                healthy_count += 1
            elif status == "WATCH" or status == "WARNING":
                warning_count += 1
            else:
                critical_count += 1

        network_health = total_health / len(preds) if preds else 100.0

        return {
            "network_health_score": round(network_health, 2),
            "summary": {
                "healthy_devices": healthy_count,
                "warning_devices": warning_count,
                "critical_devices": critical_count
            },
            "devices": device_risks
        }

    def get_root_cause_analysis(self, db: Session) -> List[dict]:
        """Retrieves active explainable root causes for all predicted anomalies."""
        preds = self.get_predictions(db)
        result = []
        for p in preds:
            if p["prediction_status"] != "NORMAL":
                result.append({
                    "device_id": p["device_id"],
                    "failure_type": p["predicted_failure_type"],
                    "root_cause_signals": p["root_cause_signals"],
                    "contributing_metrics": p["contributing_metrics"],
                    "explainability": p["explainability"],
                    "recommended_action": p["recommended_action"]
                })
        return result

    def get_network_health(self, db: Session) -> Dict[str, Any]:
        """Provides high-level network convergence health data."""
        profile = self.get_risk_profile(db)
        return {
            "network_health_score": profile["network_health_score"],
            "status": "HEALTHY" if profile["network_health_score"] > 85.0 else ("DEGRADED" if profile["network_health_score"] > 60.0 else "CRITICAL"),
            "active_anomalies_count": profile["summary"]["critical_devices"]
        }

    def get_device_prediction(self, device_id: str, db: Session) -> Dict[str, Any]:
        """Returns predictions for a single specific device."""
        preds = self.get_predictions(db)
        for p in preds:
            if p["device_id"] == device_id:
                return p
        return {"status": "error", "message": "Device not found"}

    def run_predictions_pass(self, db: Session) -> List[dict]:
        """
        Executes ML predictive models, evaluates graph dependencies,
        computes XAI explanations, and persists logs in SQLite.
        """
        devices = db.query(Device).all()
        time_now = datetime.now()
        
        predictions_output = []

        # Graph critical node centrality calculations
        critical_nodes = graph_analysis_engine.get_critical_nodes()

        for dev in devices:
            dev_id = dev.id
            
            # Fetch recent timeseries records
            history_records = db.query(TelemetryHistory)\
                .filter(TelemetryHistory.device_id == dev_id)\
                .order_by(TelemetryHistory.timestamp.desc())\
                .limit(20).all()
            
            # Convert DB history to standard dict list representation (chronological order)
            history_list = []
            for r in reversed(history_records):
                history_list.append({
                    "cpu_usage": r.cpu_usage,
                    "memory_usage": r.memory_usage,
                    "latency": r.latency,
                    "packet_loss": r.packet_loss,
                    "tunnel_health": r.tunnel_health,
                    "interface_errors": r.interface_errors
                })

            # Create current metrics state vector
            current_metrics = {
                "id": dev_id,
                "name": dev.name,
                "type": dev.type,
                "cpu_usage": dev.cpu_usage,
                "memory_usage": dev.memory_usage,
                "bgp_state": dev.bgp_state,
                "ospf_state": dev.ospf_state,
                "mpls_label_status": dev.mpls_label_status
            }

            # Map the latest metrics from history table if available
            if history_records:
                latest = history_records[0]
                current_metrics.update({
                    "rx_bandwidth": latest.rx_bandwidth,
                    "tx_bandwidth": latest.tx_bandwidth,
                    "latency": latest.latency,
                    "jitter": latest.jitter,
                    "packet_loss": latest.packet_loss,
                    "tunnel_health": latest.tunnel_health,
                    "interface_errors": latest.interface_errors,
                    "link_availability": latest.link_availability
                })
            else:
                current_metrics.update({
                    "rx_bandwidth": 10.0,
                    "tx_bandwidth": 10.0,
                    "latency": 15.0 if dev.type != "DC" else 1.0,
                    "jitter": 1.0,
                    "packet_loss": 0.0,
                    "tunnel_health": 100.0,
                    "interface_errors": 0,
                    "link_availability": 1.0
                })

            # ----------------------------------------------------
            # Model 1: Isolation Forest Outlier Analysis
            # ----------------------------------------------------
            anomaly_res = self.isolation_forest.predict(current_metrics, history_list)
            
            # ----------------------------------------------------
            # Model 2: LSTM Trend Forecast Projection
            # ----------------------------------------------------
            lstm_res = self.lstm.predict(current_metrics, history_list)

            # ----------------------------------------------------
            # Model 3: XGBoost Classifier
            # ----------------------------------------------------
            xgb_res = self.xgboost.predict(current_metrics, history_list)

            # Extract metrics
            prob = xgb_res["failure_probability"]
            conf = xgb_res["confidence"]
            failure_type = xgb_res["predicted_failure_type"]
            time_to_impact = xgb_res["time_to_impact"]

            # Override/enrich prediction logic if Isolation Forest detects an anomaly 
            # and XGBoost is unsure.
            if anomaly_res["is_anomaly"] and failure_type == "None":
                prob = max(prob, anomaly_res["anomaly_score"])
                failure_type = "Hardware Failure"
                time_to_impact = "30 Min"

            # ----------------------------------------------------
            # Graph-Based Impact Analysis (Blast Radius & SPOF)
            # ----------------------------------------------------
            graph_res = graph_analysis_engine.analyze_node_failure(dev_id)
            blast_radius = graph_res["blast_radius"]
            criticality_score = graph_res["criticality_score"]

            business_impact = {
                "affected_branches": graph_res["affected_branches"],
                "affected_users": graph_res["affected_users"],
                "affected_services": graph_res["affected_services"],
                "is_spof": graph_res["is_spof"]
            }

            # Map recommended actions
            recommended_action = "None required. Maintain baseline monitoring."
            if failure_type == "Congestion":
                recommended_action = "Adjust SDWAN interface QoS traffic shaper policies."
            elif failure_type == "IPSec Tunnel Failure":
                recommended_action = "Restart crypto daemon peer and force renegotiation."
            elif failure_type == "Routing Loop":
                recommended_action = "Re-converge routing nodes and modify OSPF cost matrices."
            elif failure_type in ["BGP Route Flap", "OSPF Instability"]:
                recommended_action = "Re-establish peering state session and check hold-timers."
            elif failure_type == "Configuration Drift":
                recommended_action = "Sync VLAN configurations and verify interface MTU parameters."
            elif failure_type == "Interface Failure":
                recommended_action = "Isolate physical interface transceiver port and failover."
            elif failure_type == "Hardware Failure":
                recommended_action = "Schedule hardware replacement for line cards."

            # Calculate Risk Level and Status
            risk_level = "LOW"
            prediction_status = "NORMAL"

            if prob > 0.85:
                risk_level = "CRITICAL"
                prediction_status = "CRITICAL"
            elif prob > 0.60:
                risk_level = "HIGH"
                prediction_status = "WARNING"
            elif prob > 0.30:
                risk_level = "MEDIUM"
                prediction_status = "WATCH"

            # ----------------------------------------------------
            # Confidence Trends and Cache Tracking
            # ----------------------------------------------------
            if dev_id not in self.confidence_caches:
                self.confidence_caches[dev_id] = [conf]
            else:
                self.confidence_caches[dev_id].append(conf)
                if len(self.confidence_caches[dev_id]) > 10:
                    self.confidence_caches[dev_id].pop(0)

            # Determine prediction trend (direction of failure probability)
            trend = "STABLE"
            if len(history_list) >= 3:
                last_prob = self.latest_predictions.get(dev_id, {}).get("failure_probability", prob)
                if prob > last_prob + 0.02:
                    trend = "UP"
                elif prob < last_prob - 0.02:
                    trend = "DOWN"

            self.trend_caches[dev_id] = trend

            # ----------------------------------------------------
            # Model 4: Explainable AI Engine Trigger
            # ----------------------------------------------------
            xai_res = explainability_engine.generate_explanation(current_metrics, {
                "predicted_failure_type": failure_type,
                "failure_probability": prob,
                "confidence": conf
            })

            # Create full prediction payload
            pred_id = str(uuid.uuid4())
            prediction_payload = {
                "prediction_id": pred_id,
                "timestamp": time_now.isoformat(),
                "created_at": time_now.isoformat(),
                "device_id": dev_id,
                "device_name": dev.name,
                "model_version": self.model_version,
                "failure_probability": round(prob, 3),
                "confidence": round(conf, 3),
                "confidence_history": self.confidence_caches[dev_id],
                "prediction_trend": trend,
                "prediction_status": prediction_status,
                "risk_level": risk_level,
                "predicted_failure_type": failure_type,
                "root_cause_signals": xai_res["root_cause_signals"],
                "contributing_metrics": xai_res["contributing_telemetry"],
                "recommended_action": recommended_action,
                "business_impact": business_impact,
                "blast_radius": blast_radius,
                "mission_criticality": round(criticality_score, 2),
                "explainability": {
                    "feature_importance": xai_res["feature_importance"],
                    "reasoning_trace": xai_res["reasoning_trace"],
                    "confidence_explanation": xai_res["confidence_explanation"]
                },
                "forecasts": lstm_res
            }

            # Update cache
            self.latest_predictions[dev_id] = prediction_payload
            predictions_output.append(prediction_payload)

            # Persist record into SQLite history table
            hist = PredictionHistory(
                prediction_id=pred_id,
                timestamp=time_now,
                created_at=time_now,
                device_id=dev_id,
                model_version=self.model_version,
                failure_probability=prob,
                confidence=conf,
                confidence_history_json=json.dumps(self.confidence_caches[dev_id]),
                prediction_trend=trend,
                prediction_status=prediction_status,
                predicted_failure_type=failure_type,
                root_cause_signals_json=json.dumps(xai_res["root_cause_signals"]),
                contributing_metrics_json=json.dumps(xai_res["contributing_telemetry"]),
                recommended_action=recommended_action,
                business_impact_json=json.dumps(business_impact),
                blast_radius=blast_radius,
                mission_criticality=criticality_score
            )
            db.add(hist)

        db.commit()
        return predictions_output

# Singleton Instance
predictive_engine = PredictiveEngineService()
