import { BrowserRouter, Routes, Route } from "react-router-dom";
import Home from "./pages/Home";
import Signup from "./pages/Signup";
import Login from "./pages/Login";
import MyTickets from "./pages/MyTickets";
import './css/Home.css';
import "./css/Login.css";
import "./css/Signup.css";
import './css/SignupForm.css';
import './css/MyTickets.css';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/signup" element={<Signup />} />
        <Route path="/login" element={<Login />} />
        <Route path="/mytickets" element={<MyTickets />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
