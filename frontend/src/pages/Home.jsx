import React from "react";
import { useNavigate } from 'react-router-dom';

const Home = () => {
    const navigate = useNavigate();

    return (
        <div className="home-container">
            <h1 className="home-title">디딤 스터디카페</h1>
            <div className="button-group">
                <button className="home-button" onClick={() => navigate('/signup')}>
                    회원가입
                </button>
                <button className="home-button" onClick={() => navigate('/login')}>
                    로그인
                </button>
            </div>
        </div>
    );
};

export default Home;
