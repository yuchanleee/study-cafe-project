import { useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";
import { IMaskInput } from "react-imask";

function SignupForm() {
    const navigate = useNavigate();

    const [formData, setFormData] = useState({
        name: "",
        age: "",
        phone: "",
    });

    const [error, setError] = useState(""); // 에러 상태 추가

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: value,
        }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError(""); // 이전 에러 초기화

        // 나이 유효성 검사 
        const age = parseInt(formData.age);
        if (isNaN(age) || age < 19) {
            setError("나이가 올바르지 않습니다. 만 19세 이상만 가입 가능합니다.");
            return;
        }

        // 전화번호 공백 제거 및 포매팅 
        const cleanedphone = formData.phone.replace(/\s/g, "")
        const fullPhone = `010-${cleanedphone}`;
        console.log("회원가입 정보:", {
            ...formData,
            phone: fullPhone,
        });

        try {
            const response = await axios.post("http://127.0.0.1:8000/signup", {
                name: formData.name,
                age,
                phone_number: fullPhone,
            });

            if (response.status === 200 || response.status === 201) {
                navigate("/"); // 홈으로 이동
            } else {
                setError("회원가입에 실패했습니다. 다시 시도해주세요.");
            }
        } catch (error) {
            console.error("회원가입 오류:", error);
            setError("회원가입 중 오류가 발생했습니다.");
        }
    };

    return (
        <form onSubmit={handleSubmit} className="form-container">
            <input
                type="text"
                name="name"
                placeholder="이름"
                value={formData.name}
                onChange={handleChange}
                required
            />
            <br />
            <input
                type="number"
                name="age"
                placeholder="나이"
                value={formData.age}
                onChange={handleChange}
                required
            />
            <br />
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

            {/* 에러 메시지 출력 영역 */}
            {error && <p className="error-text">{error}</p>}
            <br />

            <div className="button-group2">
                <button type="submit" className="submit-btn">회원가입하기</button>
                <button type="button" className="home-btn" onClick={() => window.location.href = "/"}>홈</button>
            </div>
        </form>
    );
}

export default SignupForm;
