import axios from "axios";
import { useNavigate } from "react-router-dom";

const LeaveButton = ({ isActive, seatId }) => {
    const navigate = useNavigate();

    const handleLeave = async () => {
        if (!window.confirm("퇴실 및 로그아웃 하시겠습니까?")) return;

        try {
            const token = localStorage.getItem("token");

            await axios.post("http://localhost:8000/leave", {
                seat_id: seatId,
            }, {
                headers: {
                    Authorization: `Bearer ${token}`,
                },
            });

            alert(`${seatId} 좌석에서 퇴실이 완료되었습니다.`);
            localStorage.removeItem("token");
            navigate("/");
        } catch (error) {
            console.error("퇴실 오류:", error);
            alert("퇴실 처리 중 오류가 발생했습니다.");
        }
    };

    return (
        <button onClick={handleLeave} disabled={!isActive}>
            퇴실 / 로그아웃
        </button>
    );
};

export default LeaveButton;
