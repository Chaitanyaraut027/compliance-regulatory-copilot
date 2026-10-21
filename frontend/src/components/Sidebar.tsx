import React from 'react';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import { NavView } from '../types';
import {
  LayoutDashboard,
  Upload,
  FileText,
  Search,
  Moon,
  Sun,
  LogOut,
  User,
} from 'lucide-react';

interface SidebarProps {
  currentView: NavView;
  onNavigate: (view: NavView) => void;
  isOpen: boolean;
  onClose: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentView,
  onNavigate,
  isOpen,
  onClose,
}) => {
  const { user, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();

  const navItems: { label: NavView; icon: React.ReactNode }[] = [
    { label: 'Dashboard', icon: <LayoutDashboard className="w-4 h-4" /> },
    { label: 'Upload Document', icon: <Upload className="w-4 h-4" /> },
    { label: 'Compliance Reports', icon: <FileText className="w-4 h-4" /> },
    { label: 'Search Regulations', icon: <Search className="w-4 h-4" /> },
  ];

  return (
    <>
      {/* Mobile backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-40 lg:hidden"
          onClick={onClose}
        />
      )}

      <aside
        className={`fixed top-0 bottom-0 left-0 z-50 w-64 bg-white dark:bg-[#111827] border-r border-slate-200 dark:border-slate-800 flex flex-col transition-transform duration-200 ease-in-out lg:translate-x-0 ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        {/* App Title */}
        <div className="p-5 border-b border-slate-200 dark:border-slate-800">
          <h1 className="font-bold text-base text-slate-900 dark:text-white leading-tight">
            Food Compliance Portal
          </h1>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            Standards & Safety Verification
          </p>
        </div>

        {/* User Card */}
        <div className="px-5 py-3.5 border-b border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/30">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-slate-200 dark:bg-slate-700 flex items-center justify-center text-slate-700 dark:text-slate-300 font-semibold text-xs">
              {user?.name ? user.name.charAt(0).toUpperCase() : <User className="w-4 h-4" />}
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-sm font-semibold text-slate-900 dark:text-white truncate">
                {user?.name || 'User'}
              </p>
              <p className="text-xs text-slate-500 dark:text-slate-400 truncate">
                {user?.email || 'user@example.com'}
              </p>
            </div>
          </div>
        </div>

        {/* Navigation Links */}
        <div className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          <div className="px-3 pb-2 text-[11px] font-semibold uppercase tracking-wider text-slate-400 dark:text-slate-500">
            Menu
          </div>
          {navItems.map((item) => {
            const isActive = currentView === item.label;
            return (
              <button
                key={item.label}
                onClick={() => {
                  onNavigate(item.label);
                  onClose();
                }}
                className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-sky-50 dark:bg-sky-950/50 text-sky-700 dark:text-sky-400 font-semibold shadow-xs'
                    : 'text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800/60 hover:text-slate-900 dark:hover:text-white'
                }`}
              >
                <span
                  className={
                    isActive
                      ? 'text-sky-600 dark:text-sky-400'
                      : 'text-slate-400 dark:text-slate-500'
                  }
                >
                  {item.icon}
                </span>
                <span>{item.label}</span>
              </button>
            );
          })}
        </div>

        {/* Footer Actions: Theme Toggle & Logout */}
        <div className="p-3.5 border-t border-slate-200 dark:border-slate-800 space-y-2">
          <button
            onClick={toggleTheme}
            className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-lg text-xs font-medium text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors border border-slate-200 dark:border-slate-700/60"
          >
            {theme === 'light' ? (
              <>
                <Moon className="w-3.5 h-3.5 text-slate-600 dark:text-slate-300" />
                <span>Dark Mode</span>
              </>
            ) : (
              <>
                <Sun className="w-3.5 h-3.5 text-amber-400" />
                <span>Light Mode</span>
              </>
            )}
          </button>

          <button
            onClick={logout}
            className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-lg text-xs font-medium text-rose-600 dark:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-950/30 transition-colors"
          >
            <LogOut className="w-3.5 h-3.5" />
            <span>Log Out</span>
          </button>
        </div>
      </aside>
    </>
  );
};
