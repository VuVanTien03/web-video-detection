import { Routes , Route, Navigate } from "react-router-dom";
import { ROUTERS } from "./utils/Router";
import Signup from "./User/Signup/Signup";  
import Login from "./User/Login/Login";
import LadingPage from "./User/LadingPage/LadingPage";
import Homepage from "./User/Homepage/Homepage";
import Dashboard from "./User/Dashboard/Dashboard";
import History from "./User/History/History";
import Home from "./Admin/Home/Home";
import UserList from "./Admin/UserList/UserList";
import UserProfile from "./Admin/UserProfile/UserProfile";
const RouterCustom = () => {
    return (
        <Routes>
            <Route path={ROUTERS.USER.SIGNUP} element={<Signup />} />
            <Route path={ROUTERS.USER.LOGIN} element={<Login />} />
            <Route path={ROUTERS.USER.LOATDING} element={<LadingPage />} />
            <Route path={ROUTERS.USER.HOMEPAGE} element={<Homepage />} />
            <Route path={ROUTERS.USER.DASHBOARD} element={<Dashboard />} />
            <Route path={ROUTERS.USER.HISTORY} element={<History />} />
            <Route path={ROUTERS.USER.DASHBOARD} element={<Dashboard />} />
            {/* Admin */}
            <Route path={ROUTERS.ADMIN.HOME} element={<Home />} />
            <Route path={ROUTERS.ADMIN.USERLIST} element={<UserList />} />
            <Route path={ROUTERS.ADMIN.USERPROFILE} element={<UserProfile />} />
        </Routes>
    );
};
export default RouterCustom;
