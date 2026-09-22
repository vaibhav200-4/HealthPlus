import React, { createContext, useContext, useState, ReactNode } from 'react';

interface FloatingUIContextType {
  activeModal: 'chat' | null;
  openChat: () => void;
  openVoice: () => void;
  closeAll: () => void;
}

const FloatingUIContext = createContext<FloatingUIContextType | undefined>(undefined);

export const FloatingUIProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [activeModal, setActiveModal] = useState<'chat' | null>(null);

  const openChat = () => setActiveModal('chat');
  const openVoice = () => setActiveModal('chat');
  const closeAll = () => setActiveModal(null);

  return (
    <FloatingUIContext.Provider value={{ activeModal, openChat, openVoice, closeAll }}>
      {children}
    </FloatingUIContext.Provider>
  );
};

export const useFloatingUI = () => {
  const context = useContext(FloatingUIContext);
  if (!context) {
    return {
      activeModal: null,
      openChat: () => {},
      openVoice: () => {},
      closeAll: () => {},
    };
  }
  return context;
};

