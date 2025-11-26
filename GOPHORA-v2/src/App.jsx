import React, { useEffect, useState } from 'react';
import ProtectedRoute from './components/common/ProtectedRoute';
import './App.css';
import './index.css';
import Register from './pages/Auth/Register';
import Login from './pages/Auth/Login';
import { Route, Routes } from 'react-router-dom';
import SeekerLayout from './layouts/SeekerLayout';
import SeekerDashboard from './pages/Seeker/Dashboard';
import ProviderDashboard from './pages/Provider/Dashboard';
import ProviderLayout from './layouts/ProviderLayout';
import LandingPage from './pages/Landing/LandingPage';
import Opportunities from './pages/Provider/Opportunities';
import CreateOpportunity from './pages/Provider/CreateOpportunity';
import Profile from './pages/Provider/Profile';
import SeekerOpportunities from './pages/Seeker/Opportunities';
import Applications from './pages/Seeker/Applications';
import SeekerProfile from './pages/Seeker/Profile';
import TestChat from './pages/Testchat';
import PageNotFound from './pages/PageNotFound';
import VerificationForm from './components/forms/VerificationForm';
import AboutUs from './pages/Landing/About';
import ExploreMissions from './pages/Landing/ExploreMissions';
import MainLayout from './layouts/PublicLayout';
import OpportunityDetails from './pages/Seeker/OpportunityDetails';
import api from './services/api';

function App() {
  const [authChecked, setAuthChecked] = useState(false);

  useEffect(() => {
    // Check if user session is still valid on app load
    const checkAuth = () => {
      const token = localStorage.getItem('token');
      const tokenExpiry = localStorage.getItem('token_expiry');
      const user = localStorage.getItem('user');
      
      if (token && tokenExpiry && user) {
        const expiryTime = parseInt(tokenExpiry);
        const currentTime = Date.now();
        
        // Check if token has expired
        if (currentTime < expiryTime) {
          console.log('Session is still valid, user stays logged in');
          // Token is still valid, user stays logged in
        } else {
          console.log('Session expired, clearing auth data');
          // Token expired, clear everything
          localStorage.removeItem('token');
          localStorage.removeItem('token_expiry');
          localStorage.removeItem('user');
          localStorage.removeItem('role');
        }
      }
      
      setAuthChecked(true);
    };

    checkAuth();
  }, []);

  // Don't render routes until auth is checked
  if (!authChecked) {
    return (
      <div className="flex items-center justify-center h-screen bg-[#03091d]">
        <div className="text-white text-xl">Loading...</div>
      </div>
    );
  }

  return (
    <Routes>
     <Route element={<MainLayout/>}>

       {/* Public */}
      <Route path="/" element={<LandingPage />} />
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route path='/about' element={<AboutUs/>}/>
      <Route path="/explore-missions" element={<ExploreMissions/>} />

      {/* Provider Routes */}
      <Route
        element={
          <ProtectedRoute allowedRole="provider">
            <ProviderLayout />
          </ProtectedRoute>
        }
      >
        <Route path="/provider/dashboard" element={<ProviderDashboard />} />
        <Route path="/provider/verify" element={<VerificationForm/>} />
        <Route path="/provider/opportunities" element={<Opportunities />} />
        <Route path="/provider/create-opportunity" element={<CreateOpportunity />} />
        <Route path="/provider/profile" element={<Profile />} />
      </Route>

      {/* Seeker Routes */}
      <Route
        element={
          <ProtectedRoute allowedRole="seeker">
            <SeekerLayout />
          </ProtectedRoute>
        }
      >
        <Route path="/seeker/dashboard" element={<SeekerDashboard />} />
        <Route path="/seeker/opportunities" element={<SeekerOpportunities />} />
        <Route path="/seeker/applications" element={<Applications />} />
        <Route path="/seeker/profile" element={<SeekerProfile />} />
        <Route path="/opportunity/:id" element={<OpportunityDetails />} />
      </Route>

      {/* Other routes */}
      <Route path="/chat" element={<TestChat />} />
      <Route path="*" element={<PageNotFound />} />
     </Route>
    </Routes>
  );
}

export default App;
