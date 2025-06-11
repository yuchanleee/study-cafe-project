import React, { useState } from 'react';
import { useLocation } from "react-router-dom";
import SvgComponent from '../components/SvgComponent';
import axios from "axios";

const Seatstatus = () => {
    const location = useLocation();
    const { user_pass_id } = location.state || {};


    const handleSeatClick = async (seatId) => {
        const token = localStorage.getItem("token");

        try {
            const res = await axios.post(
                "http://localhost:8000/seat",
                {
                    seat_id: seatId,
                    user_pass_id: parseInt(user_pass_id),
                },
                {
                    headers: {
                        Authorization: `Bearer ${token}`,
                    },
                }
            );
            console.log("착석 성공:", res.data);
            // UI 업데이트 등 추가 동작 필요 시 여기에
            alert(`${seatID}좌석에 착석이 완료되었습니다.`);
            navigate("/mytickets");

        } catch (error) {
            console.error("좌석 착석 실패:", error);
        }
    };


    return (
        <div className="seatstatus-container">
            <div className="seatstatus-svg-wrapper">
                <SvgComponent
                    className="seatstatus-svg"
                    handleSeatClick={handleSeatClick}
                />
            </div>
        </div>
    );
};

export default Seatstatus;
