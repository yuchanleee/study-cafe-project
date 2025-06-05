import { useState } from "react";
import axios from "axios";
import { IMaskInput } from "react-imask";
import { useNavigate } from "react-router-dom";

function Login() {
    const navigate = useNavigate();
    const [formData, setFormData] = useState({
        phone: "",
    });
    const [error, setError] = useState("");

    const handleChange = (e) => {
        setFormData({
            ...formData,
            [e.target.name]: e.target.value,
        });
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError("");



        try {
            // 전화번호 공백 제거 및 포매팅
            const cleanedphone = formData.phone.replace(/\s/g, "");
            const fullPhone = `010-${cleanedphone}`;

            const response = await axios.post("http://localhost:8000/login", {
                phone_number: fullPhone,  // 서버에서 기대하는 필드명
            });

            const { access_token } = response.data;
            localStorage.setItem("token", access_token);

            navigate("/mytickets")

        } catch (err) {
            console.error("로그인 오류:", err);
            setError("전화번호가 일치하지 않습니다.");
        }

    };

    return (
        <div className="login-container">
            <form onSubmit={handleSubmit}>
                <div className="phone-wrapper">
                    <span className="phone-prefix">010 -</span>
                    <IMaskInput
                        className="phone-input"
                        mask="0000 - 0000"
                        name="phone"
                        placeholder="전화번호"
                        value={formData.phone}
                        onChange={handleChange}
                        required
                    />
                </div>

                <br />
                <br />

                {error && <p className="error-text">{error}</p>}

                <div className="button-group2">
                    <button type="submit" className="submit-btn">
                        로그인
                    </button>
                    <button
                        type="button"
                        className="home-btn"
                        onClick={() => navigate("/")}
                    >
                        홈
                    </button>
                </div>
            </form>
        </div>
    );
}

export default Login;
