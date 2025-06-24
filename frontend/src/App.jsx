import React, { useEffect, useRef, useState } from 'react';
import styles from './App.module.css'
import MappingPoints from './components/MappingPoints/MappingPoints';

export default function App() {
  const [frame, setFrame] = useState('');
  const [fps, setFps] = useState(0);
  const [ws, setWs] = useState(null);
  const [range, setRange] = useState(defaultRange);
  const [center, setCenter] = useState(defaultCenter);
  const [corner, setCorner] = useState(defaultCorner);
  const [mappingItems, setMappingItems] = useState(defaultMappingItems);
  const [unit, setUnit] = useState(0);
  const [detectMode, setDetectMode] = useState(0);
  const [shootMode, setShootMode] = useState(0);
  const [laserMode, setLaserMode] = useState(0);
  const [logs, setLogs] = useState([]);
  const [laserCorrection, setLaserCorrection] = useState(0)
  const [resultImage, setResultImage] = useState(null)
  
  const modeSelectRef = useRef(null);
  const xInputRef = useRef(null);
  const yInputRef = useRef(null);

  const frameTimesRef = useRef([]);
  const lastFpsUpdateRef = useRef(0);
  const fileInputRef = useRef(null)

  const handleManualShoot = () => {
    const mode = modeSelectRef.current.value;
    const x = xInputRef.current.value;
    const y = yInputRef.current.value;

    ws.send(JSON.stringify({ type: 'shoot', action: 'manual', data: { mode, x, y } }));
  }

  const handleContinuousShoot = () => {
    const corners = Object.values(corner);
    // const targets = Object.values(corner);

    // corners.forEach((_, idx) => {
    //   const next = (idx + 1) % 4;
    //   targets.splice(
    //     2 * idx + 1, 0,
    //     {
    //       'x': (corners[idx].x + corners[next].x) / 2, 
    //       'y': (corners[idx].y + corners[next].y) / 2
    //     }
    //   )
    // })

    ws.send(JSON.stringify({ type: 'shoot', action: 'continuous', data: corners }));    
  }

  const handleCenterCoordinate = (e) => {
    const name = e.target.name;
    const value = parseInt(e.target.value) || 0;
    
    setCenter({ ...center, [name]: value });
    handleCornerCoordinates({ ...center, [name]: value }, range);
  }

  const handleRange = (e) => {
    const name = e.target.name;
    const value = parseInt(e.target.value) || 0;

    setRange({ ...range, [name]: value });
    handleCornerCoordinates(center, { ...range, [name]: value });
  }

  const handleCornerCoordinates = (center, range) => {
    const newCornerCoordinate = {
      'LT': { 'x': center.x + range.x, 'y': center.y + range.y },
      'RT': { 'x': center.x - range.x, 'y': center.y + range.y },
      'RB': { 'x': center.x - range.x, 'y': center.y - range.y },
      'LB': { 'x': center.x + range.x, 'y': center.y - range.y },
    }
    
    setCorner(newCornerCoordinate)
  }

  const handleCornerCoordinate = (e) => {
    const [oneCorner, coordinate] = e.target.name.split('_');
    const value = parseInt(e.target.value) || 0;

    setCorner({ ...corner, [oneCorner]: { ...corner[oneCorner], [coordinate]: value } });
  }

  const handleUnit = (e) => {
    setUnit(e.target.value);
  }

  const handleRatioCoordinates = (e) => {
    const selectedUnit = e.target.value; 
    const ratioX = 4 * selectedUnit;
    const ratioY = 3 * selectedUnit;
    const newCornerCoordinate = {
      'LT': { 'x': center.x + ratioX, 'y': center.y + ratioY },
      'RT': { 'x': center.x - ratioX, 'y': center.y + ratioY },
      'RB': { 'x': center.x - ratioX, 'y': center.y - ratioY },
      'LB': { 'x': center.x + ratioX, 'y': center.y - ratioY },
    };
    
    setCorner(newCornerCoordinate);
  }

  const handleMappingItems = (e) => {
    const [title, order, oneCoord] = e.target.name.split('_');
    const value = parseInt(e.target.value);
    
    const newMappingItem = mappingItems[title].map((coord, idx) => {
      if (idx === parseInt(order)) coord[oneCoord] = value;
      return coord;
    })  

    setMappingItems({ ...mappingItems, [title]: newMappingItem });
  }

  const saveMappingItems = () => {
    ws.send(JSON.stringify({ type: 'mapping', action: 'save', data: mappingItems }));
  }

  const loadMappingItems = () => {
    ws.send(JSON.stringify({ type: 'mapping', action: 'load' }));
  }

  const handleMapping = () => {
    ws.send(JSON.stringify({ type: 'mapping', action: 'mapping', data: mappingItems }));
  }

  const handleDetectMode = () => {
    const mode = detectMode === 0 ? 1 : 0;
    ws.send(JSON.stringify({ type: 'control', action: 'detectMode', data: mode }));
    setDetectMode(mode);
  }

  const handleShootMode = () => {
    const mode = shootMode === 0 ? 1 : 0;
    ws.send(JSON.stringify({ type: 'control', action: 'shootMode', data: mode }));
    setShootMode(mode);
  }

  const handleLaserMode = () => {
    const mode = laserMode === 0 ? 1 : 0;
    ws.send(JSON.stringify({ type: 'control', action: 'laserMode', data: { 'mode': mode, 'correctionValue': laserCorrection } }));
    setLaserMode(mode)
  }

  const handleCenterShoot = () => {
    ws.send(JSON.stringify({ type: 'shoot', action: 'manual', data: { 'mode': 'PLC', 'x': center.x, 'y': center.y } }));
  }

  const handleCapture = () => {
    ws.send(JSON.stringify({ type: 'camera', action: 'capture' }));
  }

  const handleValidation = () => {
    ws.send(JSON.stringify({ type: 'mapping', action: 'validation' }));
  }

  const handleTest = () => {
    ws.send(JSON.stringify({ type: 'shoot', action: 'manual', data: { 'mode': 'test', 'x': center.x, 'y': center.y } }));
  }

  const handleLaserCorrection = (e) => {
    const correctionValue = parseInt(e.target.value);
    setLaserCorrection(correctionValue);
  }

  const handleUpload = (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const reader = new FileReader()
    reader.onload = (event) => {
      ws.send(event.target.result);
    }
    reader.readAsArrayBuffer(file)
  }

  useEffect(() => {
    const socket = new WebSocket('ws://localhost:8765');
    socket.binaryType = 'arraybuffer';
    setWs(socket);

    let prevUrl = null;
    let nextBinaryType = null;

    socket.onmessage = async (e) => {
      if (e.data instanceof ArrayBuffer) {
        if (nextBinaryType === 'result') {
          const blob = new Blob([e.data], { type: 'image/jpeg' });
          const url = URL.createObjectURL(blob);
          setResultImage(url)
        } else {
          try {
            const blob = new Blob([e.data], { type: 'image/jpeg' });
            const url = URL.createObjectURL(blob);
  
            if (prevUrl) {
              URL.revokeObjectURL(prevUrl);
            }
            prevUrl = url;
            setFrame(url);
  
            // FPS 계산
            const now = performance.now();
            frameTimesRef.current = frameTimesRef.current.filter(t => now - t < 1000);
            frameTimesRef.current.push(now);
  
            if (now - lastFpsUpdateRef.current > 200) {
              setFps(frameTimesRef.current.length);
              lastFpsUpdateRef.current = now;
            }
          } catch (error) {
            console.error('프레임 처리 중 오류 발생:', error);
          }  
        }
        nextBinaryType = null;
      } else {
        const message = JSON.parse(e.data);

        if (message.type === 'mapping') setMappingItems(message.data);
        else if (message.type === 'message') setLogs(prevLogs => [message.message, ...prevLogs]);
        else if (message.type === 'result') nextBinaryType = 'result';
      }
    }

    socket.onopen = () => {
      console.log('웹소켓 연결 성공');
      try {
        socket.send(JSON.stringify({ type: 'camera', action: 'start' }));
      } catch (error) {
        console.error('카메라 시작 명령 전송 실패:', error);
      }
    }

    socket.onerror = (error) => {
      console.error('웹소켓 오류 발생:', error);
    }

    socket.onclose = (event) => {
      console.log(`웹소켓 연결 종료 (코드: ${event.code}, 이유: ${event.reason})`);
    };

    return () => {
      if (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING) {
        socket.close();
      }
      
      if (prevUrl) {
        URL.revokeObjectURL(prevUrl);
      }
      
      frameTimesRef.current = [];
    }
  }, [])

  return (
    <section>
      <main>
        <div className={styles.left}>
          <div className={styles.fps}>
            <span>FPS: {fps}</span>
          </div>
          <div className={styles.camera_container}>
            {frame && <img className={styles.camera} src={resultImage || frame} alt='realtime-video' />}
          </div>
        </div>
        <div className={styles.right}>
          <div className={styles.target_container}>
            <div className={styles.title}>
              <span>표적지</span>
            </div>
            <div className={styles.target}>
              <div className={styles.LT}>
                <input className={styles.target_input} type="number" name="LT_x" value={corner.LT.x} onChange={handleCornerCoordinate} />
                <input className={styles.target_input} type="number" name="LT_y" value={corner.LT.y} onChange={handleCornerCoordinate} />
              </div>
              <div className={styles.RT}>
                <input className={styles.target_input} type="number" name="RT_x" value={corner.RT.x} onChange={handleCornerCoordinate} />
                <input className={styles.target_input} type="number" name="RT_y" value={corner.RT.y} onChange={handleCornerCoordinate} />
              </div>
              <div className={styles.RB}>
                <input className={styles.target_input} type="number" name="RB_x" value={corner.RB.x} onChange={handleCornerCoordinate} />
                <input className={styles.target_input} type="number" name="RB_y" value={corner.RB.y} onChange={handleCornerCoordinate} />
              </div>
              <div className={styles.LB}>
                <input className={styles.target_input} type="number" name="LB_x" value={corner.LB.x} onChange={handleCornerCoordinate} />
                <input className={styles.target_input} type="number" name="LB_y" value={corner.LB.y} onChange={handleCornerCoordinate} />
              </div>
              <div className={styles.dot} />
              <div className={styles.center}>
                <input className={styles.target_input} type="number" name="x" value={center.x} onChange={handleCenterCoordinate} />
                <input className={styles.target_input} type="number" name="y" value={center.y} onChange={handleCenterCoordinate} />
              </div>
            </div>
            <div className={styles.target_change}>
              <div>
                <div className={styles.range}>
                  <span>상하:</span>
                  <input className={styles.target_change_input} type="number" name="x" value={range.x} onChange={handleRange} />
                  <span>좌우:</span>
                  <input className={styles.target_change_input} type="number" name="y" value={range.y} onChange={handleRange} />
                </div>
                <div className={styles.unit}>
                  <span>단위:</span>
                  <input className={styles.target_change_input} type="number" value={unit} onChange={handleUnit}/>
                  <select className={styles.unit_select} onChange={handleRatioCoordinates}>
                    {[0, 1, 2, 3, 4, 5].map((num) => <option key={num} value={unit * num}>{unit * num}</option>)}
                  </select>
                </div>
              </div>
              <button onClick={handleContinuousShoot}>연속</button>
            </div>
          </div>
          <div className={styles.manual}>
            <div>
              <select ref={modeSelectRef} className={styles.manual_mode}>
                <option value='PLC'>PLC</option>
                <option value='Pixel'>Pixel 👉 PLC</option>
              </select>
              <div className={styles.manual_input}>
                <input ref={xInputRef} type="number" />
                <input ref={yInputRef} type="number" />
              </div>
            </div>
            <button onClick={handleManualShoot}>수동</button>
          </div>
          <div className={styles.log_container}>
            {logs.map((log, idx) => (
              <p key={idx}>{log}</p>
            ))}
          </div>
        </div>
      </main>
      <footer>
        <div className={styles.mapping}>
          <div className={styles.mapping_top}>
            <span>PLC, Pixel 매핑</span>
            <div className={styles.mapping_buttons}>
              <button onClick={loadMappingItems}>불러오기</button>
              <button onClick={saveMappingItems}>저장하기</button>
              <button onClick={handleMapping}>매핑하기</button>
            </div>
          </div>
          <div className={styles.mapping_points}>
            <MappingPoints title="PLC" mappingItem={mappingItems.PLC} onMappingItems={handleMappingItems} />
            <MappingPoints title="Pixel" mappingItem={mappingItems.Pixel} onMappingItems={handleMappingItems}/>
          </div>
        </div>
        <div className={styles.control}>
          <button className={`${detectMode === 0 ? styles.off : styles.on}`} onClick={handleDetectMode}>인식</button>
          <button className={`${shootMode === 0 ? styles.off : styles.on}`} onClick={handleShootMode}>사격</button>
          <input className={styles.laser_input} type="number" name="laser" value={laserCorrection} onChange={handleLaserCorrection} />
          <button className={`${laserMode === 0 ? styles.off : styles.on}`} onClick={handleLaserMode}>레이저</button>
          <button className={styles.control_button} onClick={handleCenterShoot}>원점</button>
          <button className={styles.control_button} onClick={handleCapture}>캡처</button>
          <button className={styles.control_button} onClick={handleValidation}>검증</button>
          {/* <button className={styles.control_button} onClick={handleTest}>테스트</button> */}
          <button className={styles.control_button} onClick={() => fileInputRef.current.click()}>업로드</button>
          <input type='file' ref={fileInputRef} accept='image/*' style={{ display: 'none' }} onChange={handleUpload} />
        </div>
      </footer>
    </section>
  );
}

const defaultRange = { 'x': 0, 'y': 0 };
const defaultCenter = { 'x': 5000, 'y': 2500 };
const defaultCorner = {
  'LT': { 'x': defaultCenter.x + defaultRange.x, 'y': defaultCenter.y + defaultRange.y },
  'RT': { 'x': defaultCenter.x - defaultRange.x, 'y': defaultCenter.y + defaultRange.y },
  'RB': { 'x': defaultCenter.x - defaultRange.x, 'y': defaultCenter.y - defaultRange.y  },
  'LB': { 'x': defaultCenter.x + defaultRange.x, 'y': defaultCenter.y - defaultRange.y  },
};
const defaultMappingItems = {
  'PLC': [[0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0]],
  'Pixel': [[0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0]]
}