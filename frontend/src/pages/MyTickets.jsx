import React, { useEffect, useState } from "react";
import axios from "axios";
import dayjs from "dayjs";
import { useNavigate } from "react-router-dom";

const MyTickets = () => {
    const navigate = useNavigate();
    const [tickets, setTickets] = useState([]);
    const [passes, setPasses] = useState([]);
    const [loading, setLoading] = useState(true);
    const [currentIndex, setCurrentIndex] = useState(0);
    const [menu, setMenu] = useState("보유이용권");
    const [userInfo, setUserInfo] = useState(null);

    useEffect(() => {
        const fetchUserInfo = async () => {
            try {
                const token = localStorage.getItem("token");
                const res = await axios.get("http://localhost:8000/me", {
                    headers: {
                        Authorization: `Bearer ${token}`,
                    },
                });
                setUserInfo(res.data);
            } catch (err) {
                console.error("사용자 정보 불러오기 실패:", err);
            }
        };

        fetchUserInfo();
    }, []);

    useEffect(() => {
        const fetchTickets = async () => {
            try {
                const token = localStorage.getItem("token");
                const response = await axios.get("http://localhost:8000/user/passes", {
                    headers: {
                        Authorization: `Bearer ${token}`,
                    },
                });
                setTickets(response.data);
            } catch (error) {
                console.error("이용권 불러오기 실패:", error);
            } finally {
                setLoading(false);
            }
        };
        fetchTickets();
    }, []);

    useEffect(() => {
        if (menu === "구매") {
            const fetchPasses = async () => {
                try {
                    const res = await axios.get("http://localhost:8000/passes");
                    setPasses(res.data);
                } catch (err) {
                    console.error("이용권 목록 불러오기 실패:", err);
                }
            };
            fetchPasses();
        }
    }, [menu]);

    const handlePurchase = async (passId) => {
        try {
            const token = localStorage.getItem("token");
            await axios.post(
                "http://localhost:8000/purchase",
                { pass_id: passId },
                {
                    headers: {
                        Authorization: `Bearer ${token}`,
                    },
                }
            );
            alert("이용권 구매 완료!");

            const res = await axios.get("http://localhost:8000/user/passes", {
                headers: {
                    Authorization: `Bearer ${token}`,
                },
            });
            setTickets(res.data);
            setMenu("보유이용권");
            setCurrentIndex(0);
        } catch (err) {
            console.error("구매 실패:", err);
            alert("구매 중 오류 발생");
        }
    };

    if (loading) return <div className="loading">이용권을 불러오는 중입니다...</div>;

    return (
        <div className="mytickets-container">
            <aside className="sidebar">
                {userInfo && (
                    <div className="user-info">
                        <strong>{userInfo.name}</strong> 님
                    </div>
                )}
                <button
                    className={`menu-button ${menu === "보유이용권" ? "active" : ""}`}
                    onClick={() => setMenu("보유이용권")}
                >
                    보유 이용권
                </button>
                <button
                    className={`menu-button ${menu === "구매" ? "active" : ""}`}
                    onClick={() => setMenu("구매")}
                >
                    이용권 구매
                </button>
            </aside>
            <main className={`content ${menu === "보유이용권" ? "centered" : ""}`}>
                {menu === "보유이용권" ? (
                    tickets.length === 0 ? (
                        <div className="empty">보유 중인 이용권이 없습니다.</div>
                    ) : (
                        <div className={`ticket-wrapper ${menu === "보유이용권" ? "owned-mode" : "purchase-mode"}`}>
                            <div className={`ticket-card ${tickets[currentIndex].is_active ? "active-card" : "inactive-card"}`}>
                                <h3>{tickets[currentIndex].name}</h3>
                                <p>
                                    유형: {
                                        {
                                            time: "당일권",
                                            time_period: "시간권",
                                            day: "기간권",
                                        }[tickets[currentIndex].pass_type]
                                    }
                                </p>

                                {tickets[currentIndex].pass_type === "time_period" ? (
                                    <p>
                                        남은 시간:{" "}
                                        {tickets[currentIndex].remaining_time != null
                                            ? `${Math.floor(tickets[currentIndex].remaining_time / 60)}시간 ${tickets[currentIndex].remaining_time % 60}분`
                                            : "정보 없음"}
                                    </p>
                                ) : (
                                    <p>
                                        만료일:{" "}
                                        {tickets[currentIndex].expire_at
                                            ? dayjs(tickets[currentIndex].expire_at).format("YYYY-MM-DD HH:mm")
                                            : "정보 없음"}
                                    </p>
                                )}

                                <p className="status">
                                    {tickets[currentIndex].is_active ? "사용 중" : "미사용 중"}
                                </p>
                            </div>

                            {tickets.length > 1 && (
                                <div className="slider-buttons">
                                    <button
                                        onClick={() => setCurrentIndex((prev) => Math.max(prev - 1, 0))}
                                        disabled={currentIndex === 0}
                                    >
                                        ◀ 이전
                                    </button>
                                    <button
                                        onClick={() =>
                                            setCurrentIndex((prev) => Math.min(prev + 1, tickets.length - 1))
                                        }
                                        disabled={currentIndex === tickets.length - 1}
                                    >
                                        다음 ▶
                                    </button>
                                </div>
                            )}

                            <div className="action-buttons">
                                <button disabled={!tickets[currentIndex].is_active}>퇴실/로그아웃</button>
                                <button
                                    onClick={() => navigate('/mytickets/Seatstatus', {
                                        state: { user_pass_id: tickets[currentIndex].user_pass_id }
                                    })}
                                    disabled={tickets[currentIndex].is_active}
                                >
                                    입실
                                </button>
                            </div>
                        </div>
                    )
                ) : (
                    <div className={`ticket-wrapper ${menu === "보유이용권" ? "owned-mode" : "purchase-mode"}`}>
                        {["time", "time_period", "day"].map((type) => {
                            const typeLabel = {
                                time: "당일권",
                                time_period: "시간권",
                                day: "기간권",
                            }[type];

                            const filtered = passes.filter((p) => p.pass_type === type);
                            if (filtered.length === 0) return null;

                            return (
                                <div key={type}>
                                    <h2 className="category-title">{typeLabel}</h2>
                                    <div className="ticket-grid">
                                        {filtered.map((item) => (
                                            <div key={item.id} className="ticket-purchase-card">
                                                <h3>
                                                    {type === "day"
                                                        ? `${item.duration}일권`
                                                        : `${Math.floor(item.duration / 60)}시간권`}
                                                </h3>
                                                <p>가격: {item.price.toLocaleString()}원</p>
                                                <button onClick={() => handlePurchase(item.id)}>구매</button>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                )}
            </main>
        </div>
    );
};

export default MyTickets;
