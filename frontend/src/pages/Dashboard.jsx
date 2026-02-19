import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, AlertTriangle, CheckCircle, TrendingUp } from 'lucide-react';
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export default function Dashboard() {
    const navigate = useNavigate();
    const [customers, setCustomers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [search, setSearch] = useState("");
    const [filter, setFilter] = useState("All");

    useEffect(() => {
        fetchCustomers();
    }, []);

    const fetchCustomers = async () => {
        try {
            const res = await axios.get(`${API_URL}/customers?limit=100`);
            setCustomers(res.data);
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const filteredCustomers = customers.filter(c => {
        const matchesSearch = c.name.toLowerCase().includes(search.toLowerCase()) || c.customer_id.toString().includes(search);
        const matchesFilter = filter === "All" || c.risk_level === filter;
        return matchesSearch && matchesFilter;
    });

    const highRiskCount = customers.filter(c => c.risk_level === "High").length;
    const mediumRiskCount = customers.filter(c => c.risk_level === "Medium").length;

    // Mock intervention stats
    const interventions = Math.round(highRiskCount * 0.8);
    const moneySaved = (interventions * 15000).toLocaleString();

    return (
        <div className="space-y-6">
            {/* Stats Overview */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <StatCard label="Total Customers" value={customers.length} icon={<TrendingUp className="text-blue-500" />} />
                <StatCard label="High Risk" value={highRiskCount} icon={<AlertTriangle className="text-red-500" />} change="+12% vs last week" />
                <StatCard label="Interventions Sent" value={interventions} icon={<CheckCircle className="text-green-500" />} />
                <StatCard label="Est. Loss Prevented" value={`₹${moneySaved}`} icon={<span className="text-xl font-bold text-emerald-600">₹</span>} />
            </div>

            {/* Filters */}
            <div className="flex flex-col md:flex-row justify-between gap-4 bg-white p-4 rounded-xl shadow-sm border border-slate-100">
                <div className="relative w-full md:w-96">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 w-4 h-4" />
                    <input
                        type="text"
                        placeholder="Search by name or ID..."
                        className="w-full pl-10 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                    />
                </div>
                <div className="flex gap-2">
                    {['All', 'High', 'Medium', 'Low'].map(f => (
                        <button
                            key={f}
                            onClick={() => setFilter(f)}
                            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${filter === f ? 'bg-blue-600 text-white' : 'bg-white border border-slate-200 text-slate-600 hover:bg-slate-50'}`}
                        >
                            {f} Risk
                        </button>
                    ))}
                </div>
            </div>

            {/* Customer Grid */}
            {loading ? (
                <div className="text-center py-20 text-slate-400">Loading portfolio data...</div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                    {filteredCustomers.map(customer => (
                        <CustomerCard key={customer.customer_id} customer={customer} onClick={() => navigate(`/customer/${customer.customer_id}`)} />
                    ))}
                </div>
            )}
        </div>
    );
}

function StatCard({ label, value, icon, change }) {
    return (
        <div className="bg-white p-4 rounded-xl shadow-sm border border-slate-100 hover:shadow-md transition-shadow">
            <div className="flex justify-between items-start mb-2">
                <span className="text-slate-500 text-sm font-medium">{label}</span>
                {icon}
            </div>
            <div className="text-2xl font-bold text-slate-800">{value}</div>
            {change && <div className="text-xs text-red-500 mt-1">{change}</div>}
        </div>
    );
}

function CustomerCard({ customer, onClick }) {
    const riskColor = {
        'High': 'bg-red-50 border-red-200 text-red-700',
        'Medium': 'bg-yellow-50 border-yellow-200 text-yellow-700',
        'Low': 'bg-green-50 border-green-200 text-green-700'
    }[customer.risk_level] || 'bg-slate-50 border-slate-200';

    const scoreColor = {
        'High': 'text-red-600',
        'Medium': 'text-yellow-600',
        'Low': 'text-green-600'
    }[customer.risk_level];

    return (
        <div onClick={onClick} className="bg-white p-4 rounded-xl border border-slate-200 hover:border-blue-400 cursor-pointer transition-all hover:shadow-md group">
            <div className="flex justify-between items-start mb-3">
                <div className={`px-2 py-1 rounded text-xs font-bold border ${riskColor}`}>
                    {customer.risk_level.toUpperCase()} RISK
                </div>
                <div className={`text-lg font-bold ${scoreColor}`}>
                    {Math.round(customer.risk_score || 0)}
                </div>
            </div>
            <h3 className="font-semibold text-slate-800 group-hover:text-blue-600 truncate">{customer.name}</h3>
            <div className="text-xs text-slate-500 mb-4">ID: #{customer.customer_id}</div>

            <div className="space-y-2 text-sm text-slate-600">
                <div className="flex justify-between">
                    <span>Income</span>
                    <span className="font-medium">₹{(customer.income / 1000).toFixed(1)}k</span>
                </div>
                <div className="flex justify-between">
                    <span>Loan</span>
                    <span className="font-medium">₹{(customer.loan_amount / 100000).toFixed(1)}L</span>
                </div>
            </div>
        </div>
    )
}
