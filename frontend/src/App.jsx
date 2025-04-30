import React, { useEffect, useState } from 'react';
import styles from './App.module.css'

export default function App() {
  const [frame, setFrame] = useState('');

  useEffect(() => {
    const socket = new WebSocket('ws://localhost:8765');
    socket.binaryType = 'arraybuffer';
    let prevUrl = null;

    socket.onmessage = async (e) => {
      const blob = new Blob([e.data], { type: 'image/jpeg' });
      const url = URL.createObjectURL(blob)

      if (prevUrl) {
        URL.revokeObjectURL(prevUrl);
      }
      prevUrl = url;

      setFrame(url);
    }

    socket.onopen = () => {
      console.log('웹소켓 연결 성공');
      socket.send(JSON.stringify({ type: 'camera', action: 'start'}))
    }

    return () => {
      socket.close();
      if (prevUrl) {
        URL.revokeObjectURL(prevUrl);
      }
    }
  }, [])

  return (
    <main className={styles.container}>
      <div className={styles.left}>
        <span>FPS: </span>
        <div className={styles.camera_container}>
          <img className={styles.camera} src={frame} alt='realtime-video' />
        </div>
      </div>
      <div className={styles.right}>
        right
      </div>
    </main>
  );
}

