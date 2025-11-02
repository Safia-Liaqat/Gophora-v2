import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { APIURL } from '../../services/api.js'

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
        }
      } catch (err) {
        console.error("Error fetching countries:", err);
        setError("Unable to load countries. Please refresh.");
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

  // ✅ Safe, production-grade submission with error handling
  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(""); // Assuming you have a state like: const [error, setError] = useState("");
    setLoading(true); // Assuming you have a state like: const [loading, setLoading] = useState(false);

    // This payload object is the most important part.
    // The keys (e.g., fullName, organizationName) must match exactly what your
    // frontend form state uses, and the final keys sent in the body
    // must match the backend's 'RegisterRequest' schema.
    const payload = {
      email: formData.email,
      password: formData.password,
      full_name: formData.fullName,
      role: role, // 'role' is passed down as a prop
      country: formData.country,
      city: formData.city,
      skills: formData.skills,
      // This key MUST be 'organizationName' to match the backend API schema
      organizationName: formData.organizationName,
      website: formData.website,
    };

    try {
      const response = await fetch(`${APIURL}/api/auth/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        // Get the specific error message from the backend's JSON response
        const errorData = await response.json();
        // The backend sends error details in a field named 'detail'
        throw new Error(errorData.detail || "An unknown error occurred.");
      }

      // On successful registration, you can navigate to the login page
      navigate('/login'); // Assuming you have: const navigate = useNavigate();

    } catch (err) {
      // Set the error message to display it in the UI
      setError(err.message);
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

      {/* Country Dropdown */}
      <select
        name="country"
        value={formData.country}
        onChange={(e) =>
          setFormData({ ...formData, country: e.target.value, city: "" })
        }
        required
        className="bg-white/5 border border-white/10 text-white placeholder-gray-400 
                   p-3 rounded-xl focus:outline-none focus:ring-2 
                   focus:ring-[#9E7BFF] transition-all duration-300"
      >
        <option value="">Select Country</option>
        {countries.map((country) => (
          <option key={country.name} value={country.name} className="text-black">
            {country.name}
          </option>
        ))}
      </select>

      {/* City Dropdown */}
      <select
        name="city"
        value={formData.city}
        onChange={handleChange}
        required
        disabled={!formData.country || loadingCities}
        className="bg-white/5 border border-white/10 text-white placeholder-gray-400 
                   p-3 rounded-xl focus:outline-none focus:ring-2 
                   focus:ring-[#9E7BFF] transition-all duration-300 disabled:opacity-50"
      >
        <option value="">
          {loadingCities
            ? "Loading cities..."
            : formData.country
            ? "Select City"
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
