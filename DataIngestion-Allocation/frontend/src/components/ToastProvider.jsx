import React, { createContext, useContext, useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X } from 'lucide-react';

const ToastContext = createContext(null);

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);

  const addToast = useCallback((message, type = 'info', duration = 4000) => {
    const id = Date.now().toString();
    setToasts(prev => [...prev, { id, message, type }]);

    // For errors, show longer (8 seconds)
    const displayDuration = type === 'error' ? 8000 : duration;
    
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== id));
    }, displayDuration);
  }, []);

  const removeToast = useCallback((id) => {
    setToasts(prev => prev.filter(t => t.id !== id));
  }, []);

  return (
    <ToastContext.Provider value={{ addToast }}>
      {children}
      <div className="fixed top-6 right-6 z-50 flex flex-col gap-3 pointer-events-none max-w-md">
        <AnimatePresence>
          {toasts.map(toast => {
            // Determine if message is long
            const isLongMessage = toast.message && toast.message.length > 100;
            const maxHeight = isLongMessage ? 'max-h-96' : 'max-h-24';
            
            return (
              <motion.div
                key={toast.id}
                initial={{ opacity: 0, x: 50 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, scale: 0.9, transition: { duration: 0.2 } }}
                className={`pointer-events-auto px-5 py-3 rounded shadow-xl border font-bold text-sm flex items-start gap-3 ${maxHeight} overflow-y-auto ${
                  toast.type === 'success' ? 'bg-[#1A1714] text-accent-green border-accent-green' :
                  toast.type === 'error' ? 'bg-[#1A1714] text-accent-red border-accent-red' :
                  'bg-[#1A1714] text-text-primary border-border'
                }`}
              >
                <div className="flex-shrink-0 mt-0.5">
                  {toast.type === 'success' && <span className="w-2 h-2 rounded-full bg-accent-green block"></span>}
                  {toast.type === 'error' && <span className="w-2 h-2 rounded-full bg-accent-red block"></span>}
                  {toast.type === 'info' && <span className="w-2 h-2 rounded-full bg-accent-blue block"></span>}
                </div>
                <div className="flex-grow break-words whitespace-pre-wrap text-xs leading-relaxed">
                  {toast.message}
                </div>
                <button
                  onClick={() => removeToast(toast.id)}
                  className="flex-shrink-0 text-current opacity-60 hover:opacity-100 transition-opacity"
                >
                  <X size={16} />
                </button>
              </motion.div>
            );
          })}
        </AnimatePresence>
      </div>
    </ToastContext.Provider>
  );
}

export const useToast = () => {
  const context = useContext(ToastContext);
  if (!context) throw new Error("useToast must be used within ToastProvider");
  return context.addToast;
};
