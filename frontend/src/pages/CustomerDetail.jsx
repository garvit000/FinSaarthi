import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';
import { ArrowLeft, AlertTriangle, Check, X } from 'lucide-react';

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export default function CustomerDetail() {
    const { id } = useParams();
    const navigate = useNavigate();
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchCustomerDetail();
    }, [id]);

    const fetchCustomerDetail = async () => {
        try {
            const res = await axios.get(`${API_URL}/customer/${id}`);
            setData(res.data);
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    if (loading) return <div className="p-10 text-center">Loading customer details...</div>;
    if (!data) return <div className="p-10 text-center text-red-500">Customer not found</div>;

    const { profile, risk_score, transactions } = data;
    const currentScore = risk_score ? Math.round(risk_score.score) : 0;

    // Mock risk history for chart
    const riskHistory = Array.from({ length: 10 }, (_, i) => ({
        day: `Day ${i * 3}`,
        score: Math.max(0, Math.min(100, currentScore + (Math.random() * 20 - 10)))
    })).sort((a, b) => a.day.localeCompare(b.day)); // Simple sort

    // Parse risk factors
    let riskFactors = [];
    try {
        if (risk_score && risk_score.risk_factors) {
            // If it's stored as JSON string or object
            riskFactors = typeof risk_score.risk_factors === 'string' ? JSON.parse(risk_score.risk_factors) : risk_score.risk_factors;
        }
    } catch (e) { console.error("Error parsing risk factors", e); }

    const riskLevel = currentScore > 70 ? 'High' : currentScore > 30 ? 'Medium' : 'Low';
    const riskColor = riskLevel === 'High' ? 'text-red-600' : riskLevel === 'Medium' ? 'text-yellow-600' : 'text-green-600';
    const bgRiskColor = riskLevel === 'High' ? 'bg-red-50 border-red-200' : riskLevel === 'Medium' ? 'bg-yellow-50 border-yellow-200' : 'bg-green-50 border-green-200';

    return (
        <div className="space-y-6">
            <button onClick={() => navigate('/')} className="flex items-center text-slate-500 hover:text-blue-600 transition-colors">
                <ArrowLeft className="w-4 h-4 mr-1" /> Back to Dashboard
            </button>

            {/* Header Card */}
            <div className={`p-6 rounded-xl border ${bgRiskColor} shadow-sm grid grid-cols-1 md:grid-cols-3 gap-6`}>
                <div className="md:col-span-2">
                    <h1 className="text-3xl font-bold text-slate-800 mb-2">{profile.name}</h1>
                    <div className="flex gap-4 text-sm text-slate-600">
                        <span>ID: #{profile.customer_id}</span>
                        <span>•</span>
                        <span>Age: {profile.age}</span>
                        <span>•</span>
                        <span>Joined: {new Date(profile.join_date).toLocaleDateString()}</span>
                    </div>
                </div>
                <div className="flex flex-col items-center justify-center border-l border-slate-200/50 pl-6">
                    <div className="text-sm font-medium text-slate-500 uppercase tracking-wider">Current Risk Score</div>
                    <div className={`text-5xl font-bold ${riskColor} my-2`}>{currentScore}</div>
                    <div className={`px-3 py-1 rounded-full text-xs font-bold text-white ${riskLevel === 'High' ? 'bg-red-500' : riskLevel === 'Medium' ? 'bg-yellow-500' : 'bg-green-500'}`}>
                        {riskLevel.toUpperCase()} RISK
                    </div>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Financial Profile */}
                <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-100">
                    <h3 className="text-lg font-bold text-slate-800 mb-4">Financial Profile</h3>
                    <div className="space-y-4">
                        <div className="flex justify-between p-3 bg-slate-50 rounded-lg">
                            <span className="text-slate-500">Monthly Income</span>
                            <span className="font-semibold">₹{(profile.income).toLocaleString()}</span>
                        </div>
                        <div className="flex justify-between p-3 bg-slate-50 rounded-lg">
                            <span className="text-slate-500">Total Loan</span>
                            <span className="font-semibold">₹{(profile.loan_amount).toLocaleString()}</span>
                        </div>
                        <div className="flex justify-between p-3 bg-slate-50 rounded-lg">
                            <span className="text-slate-500">EMI Amount</span>
                            <span className="font-semibold">₹{(profile.emi_amount).toLocaleString()}</span>
                        </div>
                        <div className="mt-4 pt-4 border-t border-slate-100">
                            <h4 className="text-sm font-semibold mb-2">Intervention Plan</h4>
                            {riskLevel === 'High' ? (
                                <button className="w-full py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors">
                                    Initiate Counseling Call
                                </button>
                            ) : (
                                <div className="text-sm text-slate-400 text-center italic">No intervention needed</div>
                            )}
                        </div>
                    </div>
                </div>

                {/* Risk Trend */}
                <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-100 lg:col-span-2">
                    <h3 className="text-lg font-bold text-slate-800 mb-4">Risk Scote Trend (Last 30 Days)</h3>
                    <div className="h-64">
                        <ResponsiveContainer width="100%" height="100%">
                            <LineChart data={riskHistory}>
                                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                                <XAxis dataKey="day" hide />
                                <YAxis domain={[0, 100]} />
                                <Tooltip />
                                <Line type="monotone" dataKey="score" stroke="#2563eb" strokeWidth={3} dot={{ r: 4 }} />
                            </LineChart>
                        </ResponsiveContainer>
                    </div>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Transaction History */}
                <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-100 lg:col-span-2">
                    <h3 className="text-lg font-bold text-slate-800 mb-4">Recent Transactions</h3>
                    <div className="overflow-x-auto">
                        <table className="w-full text-left text-sm">
                            <thead className="bg-slate-50 text-slate-500">
                                <tr>
                                    <th className="p-3">Date</th>
                                    <th className="p-3">Merchant</th>
                                    <th className="p-3">Category</th>
                                    <th className="p-3 text-right">Amount</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-100">
                                {transactions.map((tx, i) => (
                                    <tr key={i} className="hover:bg-slate-50">
                                        <td className="p-3 text-slate-600">{new Date(tx.date).toLocaleDateString()}</td>
                                        <td className="p-3 font-medium text-slate-800">{tx.merchant}</td>
                                        <td className="p-3 text-slate-500">
                                            <span className="px-2 py-1 bg-slate-100 rounded text-xs">{tx.category}</span>
                                        </td>
                                        <td className={`p-3 text-right font-medium ${tx.type === 'CREDIT' ? 'text-green-600' : 'text-slate-800'}`}>
                                            {tx.type === 'CREDIT' ? '+' : '-'}₹{tx.amount.toLocaleString()}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>

                {/* Risk Factors */}
                <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-100">
                    <h3 className="text-lg font-bold text-slate-800 mb-4">Top Stress Indicators</h3>
                    <div className="space-y-4">
                        {riskFactors && riskFactors.length > 0 ? (
                            riskFactors.map((f, i) => (
                                <div key={i} className="flex items-center gap-3">
                                    <div className="w-8 h-8 rounded-full bg-red-100 flex items-center justify-center text-red-600 font-bold">
                                        {i + 1}
                                    </div>
                                    <div>
                                        <div className="font-medium text-slate-800 capitalize">{f.feature.replace(/_/g, ' ')}</div>
                                        <div className="text-xs text-slate-500">High Impact Factor</div>
                                    </div>
                                </div>
                            ))
                        ) : (
                            <div className="text-slate-400 text-center py-4">No specific risk factors identified yet.</div>
                        )}

                        <div className="mt-6 p-4 bg-blue-50 rounded-lg text-sm text-blue-800">
                            <strong>AI Analysis:</strong> This customer is showing signs of {riskLevel.toLowerCase()} financial stress based on recent spending patterns.
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
