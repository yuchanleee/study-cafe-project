import React, { useEffect, useState } from "react";
import axios from "axios";
import dayjs from "dayjs";

const MyTickets = () => {
    const [tickets, setTickets] = useState([]);
    const [loading, setLoading] = useState(true);
    const [currentIndex, setCurrentIndex] = useState(0);
    const [menu, setMenu] = useState("보유이용권");

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

    if (loading) return <div className="loading">이용권을 불러오는 중입니다...</div>;

    return (
        <div className="mytickets-container">
            <aside className="sidebar">
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
            <main className="content">
                {menu === "보유이용권" ? (
                    tickets.length === 0 ? (
                        <div className="empty">보유 중인 이용권이 없습니다.</div>
                    ) : (
                        <div className="ticket-wrapper">
                            <div
                                className={`ticket-card ${tickets[currentIndex].is_active ? "active-card" : "inactive-card"
                                    }`}
                            >
                                <h3>{tickets[currentIndex].name}</h3>
                                <p>유형: {tickets[currentIndex].pass_type}</p>
                                {tickets[currentIndex].pass_type === "time" ? (
                                    <p>
                                        남은 시간:{" "}
                                        {tickets[currentIndex].remaining_time != null
                                            ? `${Math.floor(tickets[currentIndex].remaining_time / 60)}시간 ${tickets[currentIndex].remaining_time % 60
                                            }분`
                                            : "정보 없음"}
                                    </p>
                                ) : (
                                    <p>
                                        만료일: {dayjs(tickets[currentIndex].expire_at).format("YYYY-MM-DD")}
                                    </p>
                                )}
                                <p className="status">
                                    {tickets[currentIndex].is_active ? "사용 중" : "미사용"}
                                </p>
                            </div>

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

                            <div className="action-buttons">
                                <button disabled={!tickets[currentIndex].is_active}>퇴실</button>
                                <button disabled={tickets[currentIndex].is_active}>입실</button>
                            </div>
                        </div>
                    )
                ) : (
                    <div className="empty">이용권 구매 페이지 (구현 예정)</div>
                )}
            </main>
        </div>
    );
};

export default MyTickets;
