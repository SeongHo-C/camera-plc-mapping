import React, { useEffect } from 'react';
import styles from './App.module.css'

export default function App() {

  useEffect(() => {
    const socket = new WebSocket('ws://localhost:8765')

    socket.onmessage = async (e) => {
      const data = JSON.parse(e.data);
      console.log(data);
    }

    socket.onopen = () => {
      console.log('웹소켓 연결 완료');
    }

    return () => {
      socket.close();
    }
  }, [])

  return (
    <main className={styles.container}>
      <div className={styles.left}>
        <span>FPS: </span>
        <div className={styles.camera_container}>

        </div>
      </div>
      <div className={styles.right}>
        right
      </div>
    </main>
  );
}

