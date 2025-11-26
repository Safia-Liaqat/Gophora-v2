import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import api, { APIURL } from '../../services/api.js'

export default function RegisterForm({ role, setRole }) {
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    password: "",
    confirmPassword: "",
    country: "",
    city: "",
    skills: "",
    organizationName: "",
    website: "",
  });

  const [countries, setCountries] = useState([]);
  const [cities, setCities] = useState([]);
  const [loading, setLoading] = useState(false);
  const [loadingCities, setLoadingCities] = useState(false);
  const [error, setError] = useState(null);

  const navigate = useNavigate();

  // ✅ Fetch countries on mount
  useEffect(() => {
    const fetchCountries = async () => {
      try {
        const res = await fetch("https://countriesnow.space/api/v0.1/countries");
        if (!res.ok) throw new Error("Failed to fetch countries.");
        const data = await res.json();
        if (data.data) {
          const countryList = data.data.map((c) => ({
            name: c.country,
            cities: c.cities,
          }));
          setCountries(countryList);
          setError(null); // Clear any previous errors
        }
      } catch (err) {
        console.error("Error fetching countries:", err);
        // Don't set error - just log it. Countries are optional.
        setCountries([{ name: "Other", cities: ["Not specified"] }]);
      }
    };
    fetchCountries();
  }, []);

  // ✅ Update cities when a country is selected
  useEffect(() => {
    if (!formData.country) return;
    setLoadingCities(true);
    const selectedCountry = countries.find(
      (c) => c.name === formData.country
    );
    if (selectedCountry) {
      setCities(selectedCountry.cities.sort());
    } else {
      setCities([]);
    }
    setLoadingCities(false);
  }, [formData.country, countries]);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    // Validate passwords match
    if (formData.password !== formData.confirmPassword) {
      setError("Passwords do not match");
      setLoading(false);
      return;
    }

    // Validate password length
    if (formData.password.length < 6) {
      setError("Password must be at least 6 characters long");
      setLoading(false);
      return;
    }

    // Backend expects: email, password, full_name, role
    const payload = {
      email: formData.email,
      password: formData.password,
      full_name: formData.name,
      role: role,
    };

    try {
      const response = await api.post('/api/auth/register', payload);
      const data = response.data;
      
      // Calculate expiry time (24 hours from now)
      const expiryTime = Date.now() + (data.expires_in * 1000);
      
      // Save token, expiry, and user data to localStorage
      localStorage.setItem('token', data.access_token);
      localStorage.setItem('token_expiry', expiryTime.toString());
      localStorage.setItem('user', JSON.stringify(data.user));

      // Update profile with additional info
      if (formData.country || formData.city || formData.skills || formData.organizationName) {
        try {
          const profilePayload = {
            country: formData.country,
            city: formData.city,
            skills: formData.skills ? formData.skills.split(',').map(s => s.trim()) : [],
            company_name: formData.organizationName,
            company_website: formData.website,
          };

          await api.put(`/api/users/${data.user.id}/profile`, profilePayload, {
            headers: {
              'Authorization': `Bearer ${data.access_token}`
            }
          });
        } catch (profileErr) {
          console.error("Profile update failed:", profileErr);
          // Continue anyway - user is registered
        }
      }

      // Navigate to appropriate dashboard
      navigate(role === 'seeker' ? '/seeker/dashboard' : '/provider/dashboard');

    } catch (err) {
      setError(err.response?.data?.detail || err.message || "Registration failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-5">
      {error && (
        <div className="bg-red-500/20 border border-red-500 text-red-300 p-3 rounded-lg text-center">
          {error}
        </div>
      )}

      {/* Common Fields */}
      {["name", "email", "password", "confirmPassword"].map((field) => (
        <input
          key={field}
          type={
            field === "password" || field === "confirmPassword"
              ? "password"
              : field === "email"
              ? "email"
              : "text"
          }
          name={field}
          value={formData[field]}
          onChange={handleChange}
          placeholder={
            field === "confirmPassword"
              ? "Confirm Password"
              : field.charAt(0).toUpperCase() + field.slice(1)
          }
          required
          className="bg-white/5 border border-white/10 text-white placeholder-gray-400 
                     p-3 rounded-xl focus:outline-none focus:ring-2 
                     focus:ring-[#9E7BFF] transition-all duration-300"
        />
      ))}

      {/* Country Dropdown - Optional */}
      <select
        name="country"
        value={formData.country}
        onChange={(e) =>
          setFormData({ ...formData, country: e.target.value, city: "" })
        }
        className="bg-white/5 border border-white/10 text-white placeholder-gray-400 
                   p-3 rounded-xl focus:outline-none focus:ring-2 
                   focus:ring-[#9E7BFF] transition-all duration-300"
      >
        <option value="">Select Country (Optional)</option>
        {countries.map((country) => (
          <option key={country.name} value={country.name} className="text-black">
            {country.name}
          </option>
        ))}
      </select>

      {/* City Dropdown - Optional */}
      <select
        name="city"
        value={formData.city}
        onChange={handleChange}
        disabled={!formData.country || loadingCities}
        className="bg-white/5 border border-white/10 text-white placeholder-gray-400 
                   p-3 rounded-xl focus:outline-none focus:ring-2 
                   focus:ring-[#9E7BFF] transition-all duration-300 disabled:opacity-50"
      >
        <option value="">
          {loadingCities
            ? "Loading cities..."
            : formData.country
            ? "Select City (Optional)"
            : "Select Country first"}
        </option>
        {cities.map((city) => (
          <option key={city} value={city} className="text-black">
            {city}
          </option>
        ))}
      </select>

      {/* Conditional Fields */}
      {role === "seeker" && (
        <textarea
          name="skills"
          value={formData.skills}
          onChange={handleChange}
          placeholder="List your key skills (e.g. React, Python, UI Design)"
          rows="3"
          className="bg-white/5 border border-white/10 text-white placeholder-gray-400 
                     p-3 rounded-xl focus:outline-none focus:ring-2 
                     focus:ring-[#9E7BFF] transition-all duration-300"
        />
      )}

      {role === "provider" && (
        <>
          <input
            type="text"
            name="organizationName"
            value={formData.organizationName}
            onChange={handleChange}
            placeholder="Organization / Company Name"
            required
            className="bg-white/5 border border-white/10 text-white placeholder-gray-400 
                       p-3 rounded-xl focus:outline-none focus:ring-2 
                       focus:ring-[#9E7BFF] transition-all duration-300"
          />
          <input
            type="url"
            name="website"
            value={formData.website}
            onChange={handleChange}
            placeholder="Website or LinkedIn (optional)"
            className="bg-white/5 border border-white/10 text-white placeholder-gray-400 
                       p-3 rounded-xl focus:outline-none focus:ring-2 
                       focus:ring-[#9E7BFF] transition-all duration-300"
          />
        </>
      )}

      {/* Submit Button */}
      <button
        type="submit"
        disabled={loading}
        className={`w-full py-3 rounded-xl font-semibold text-white tracking-wide
                   bg-gradient-to-r from-[#7F4DFF] to-[#9E7BFF]
                   hover:shadow-[0_0_30px_rgba(158,123,255,0.6)]
                   transition-all duration-300 ${
                     loading ? "opacity-60 cursor-not-allowed" : ""
                   }`}
      >
        {loading
          ? "Registering..."
          : `Register as ${
              role === "seeker" ? "Opportunity Seeker" : "Provider"
            }`}
      </button>

      {/* Back Button */}
      <button
        type="button"
        onClick={() => setRole("")}
        className="mt-3 text-sm text-gray-400 hover:text-gray-200 transition"
      >
        ← Go back
      </button>
    </form>
  );
}
