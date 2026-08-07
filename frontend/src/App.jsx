import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import { ProtectedRoute, AdminRoute } from './components/ProtectedRoute'
import Home from './pages/Home'
import Login from './pages/Login'
import Register from './pages/Register'
import ForgotPassword from './pages/ForgotPassword'
import ResetPassword from './pages/ResetPassword'
import PostDetail from './pages/PostDetail'
import PostCreate from './pages/PostCreate'
import PostEdit from './pages/PostEdit'
import UserProfile from './pages/UserProfile'
import Settings from './pages/Settings'
import NotFound from './pages/NotFound'
import AdminDashboard from './pages/admin/AdminDashboard'

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<Home />} />
        <Route path="login" element={<Login />} />
        <Route path="register" element={<Register />} />
        <Route path="forgot-password" element={<ForgotPassword />} />
        <Route path="reset-password" element={<ResetPassword />} />
        <Route path="posts/:id" element={<PostDetail />} />
        <Route path="users/:id" element={<UserProfile />} />

        <Route element={<ProtectedRoute />}>
          <Route path="posts/new" element={<PostCreate />} />
          <Route path="posts/:id/edit" element={<PostEdit />} />
          <Route path="settings" element={<Settings />} />
        </Route>

        <Route element={<AdminRoute />}>
          <Route path="admin" element={<AdminDashboard />} />
        </Route>

        <Route path="*" element={<NotFound />} />
      </Route>
    </Routes>
  )
}
