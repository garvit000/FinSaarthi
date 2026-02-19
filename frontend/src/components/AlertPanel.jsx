import { useState, useEffect, useRef } from 'react';
import { AlertCircle, X, ExternalLink } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
const WS_URL = API_URL.replace(/^http/, "ws") + "/ws/simulate";

export default function AlertPanel() {
    const [alerts, setAlerts] = useState([]);
    const [isConnected, setIsConnected] = useState(false);
    const ws = useRef(null);
    const navigate = useNavigate();

    useEffect(() => {
        // Connect to WebSocket
        ws.current = new WebSocket(WS_URL);

        ws.current.onopen = () => {
            console.log("WS Connected");
            setIsConnected(true);
        };

        ws.current.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.alert) {
                playAlertSound();
                setAlerts(prev => [data, ...prev].slice(0, 5)); // Keep last 5
            }
        };

        ws.current.onclose = () => setIsConnected(false);

        return () => {
            if (ws.current) ws.current.close();
        };
    }, []);

    const playAlertSound = () => {
        // Simple beep using AudioContext or just console for now to avoid auto-play issues
        // In real app, use a sound file
        console.log("BEEP! Risk Alert");
    };

    const removeAlert = (index) => {
        setAlerts(prev => prev.filter((_, i) => i !== index));
    };

    if (alerts.length === 0) return null;

    return (
        <div className="fixed bottom-6 right-6 w-80 space-y-3 z-50">
            {alerts.map((alert, index) => (
                <div key={index} className="bg-white border-l-4 border-red-500 shadow-lg p-4 rounded-r-lg flex items-start justify-between animate-slide-in">
                    <div>
                        <div className="flex items-center gap-2 text-red-600 font-bold">
                            <AlertCircle size={16} />
                            <span>Risk Spike Detected!</span>
                        </div>
                        <div className="mt-1 text-sm text-slate-700">
                            <strong>{alert.name || `Customer #${alert.customer_id}`}</strong>
                            <div className="text-xs text-slate-500">Score surged to {Math.round(alert.new_score)}</div>
                        </div>
                        <button
                            onClick={() => navigate(`/customer/${alert.customer_id}`)}
                            className="mt-2 text-xs flex items-center text-blue-600 hover:text-blue-800 font-medium"
                        >
                            View Profile <ExternalLink size={10} className="ml-1" />
                        </button>
                    </div>
                    <button onClick={() => removeAlert(index)} className="text-slate-400 hover:text-slate-600">
                        <X size={16} />
                    </button>
                </div>
            ))}
        </div>
    );
}
