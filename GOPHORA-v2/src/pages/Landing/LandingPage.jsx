import React, { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import Navbar from '../../components/common/Navbar'
import Footer from '../../components/common/Footer'
import HeroSection from './HeroSection'
import HowItWorks from './HowItWorks'
import Opportunities from './Opportunities'
import PricingPlans from './PricingPlans'
import Testimonials from './Testimonials'

function LandingPage() {
  const navigate = useNavigate();

  useEffect(() => {
    // If user is already logged in, redirect to their dashboard
    const token = localStorage.getItem('token');
    const role = localStorage.getItem('role');
    
    if (token && role) {
      navigate(`/${role}/dashboard`);
    }
  }, [navigate]);

  return (
    <div className="min-h-screen flex flex-col">
      <main className="flex-1  ">
        <HeroSection/>
        <HowItWorks/>
        <Opportunities/>
        <PricingPlans/>
        <Testimonials/>
      </main>
      <Footer />
    </div>
  )
}

export default LandingPage
