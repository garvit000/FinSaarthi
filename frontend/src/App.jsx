import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import CustomerDetail from './pages/CustomerDetail';
import AlertPanel from './components/AlertPanel';

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-slate-50">
        <nav className="bg-white border-b border-slate-200 px-6 py-4 flex justify-between items-center shadow-sm sticky top-0 z-40">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center text-white font-bold">L</div>
            <h1 className="text-xl font-bold text-slate-800">Lighthouse <span className="text-slate-400 font-normal text-sm">Intervention Engine</span></h1>
          </div>
          <div className="flex items-center gap-4">
            <span className="text-sm text-slate-500">System Status: Active</span>
            <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div>
          </div>
        </nav>

        <main className="p-6 max-w-7xl mx-auto">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/customer/:id" element={<CustomerDetail />} />
          </Routes>
        </main>

        <AlertPanel />
      </div>
    </BrowserRouter>
  );
}

export default App;
