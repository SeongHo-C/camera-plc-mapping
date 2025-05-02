import React, { useEffect, useRef, useState } from 'react';
import styles from './App.module.css'

export default function App() {
  const [frame, setFrame] = useState('');
  const [ws, setWs] = useState(null);

  const modeSelectRef = useRef(null)
  const xInputRef = useRef(null)
  const yInputRef = useRef(null)

  const handleManualShoot = () => {
    const mode = modeSelectRef.current.value;
    const x = xInputRef.current.value;
    const y = yInputRef.current.value;

    ws.send(JSON.stringify({ type: 'shoot', action: 'manual', data: {mode, x, y}}))
  }

  useEffect(() => {
    const socket = new WebSocket('ws://localhost:8765');
    socket.binaryType = 'arraybuffer';
    setWs(socket)

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
          {frame && <img className={styles.camera} src={frame} alt='realtime-video' />}
        </div>
      </div>
      <div className={styles.right}>
        <div className={styles.manual}>
          <select ref={modeSelectRef} className={styles.manual_mode}>
            <option value='PLC'>PLC</option>
            <option value='Pixel'>Pixel 👉 PLC</option>
          </select>
          <div>
            <input ref={xInputRef} type="number" />
            <input ref={yInputRef} type="number" />
            <button onClick={handleManualShoot}>수동</button>
          </div>
        </div>
      </div>
    </main>
  );
}

