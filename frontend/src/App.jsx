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
  const [shootMode, setShootMode] = useState(0);
  const [laserMode, setLaserMode] = useState(0);

  const modeSelectRef = useRef(null);
  const xInputRef = useRef(null);
  const yInputRef = useRef(null);

  const frameTimesRef = useRef([]);
  const lastFpsUpdateRef = useRef(0);

  const handleManualShoot = () => {
    const mode = modeSelectRef.current.value;
    const x = xInputRef.current.value;
    const y = yInputRef.current.value;

    ws.send(JSON.stringify({ type: 'shoot', action: 'manual', data: { mode, x, y } }));
  }

  const handleContinuousShoot = () => {
    ws.send(JSON.stringify({ type: 'shoot', action: 'continuous', data: Object.values(corner) }));    
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
      'LB': { 'x': center.x + range.x, 'y': center.y - range.y },
      'RB': { 'x': center.x - range.x, 'y': center.y - range.y },
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
      'LB': { 'x': center.x + ratioX, 'y': center.y - ratioY },
      'RB': { 'x': center.x - ratioX, 'y': center.y - ratioY },
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

  const handleShootMode = () => {
    const mode = shootMode === 0 ? 1 : 0;
    ws.send(JSON.stringify({ type: 'control', action: 'shootMode', data: mode }));
    setShootMode(mode);
  }

  useEffect(() => {
    const socket = new WebSocket('ws://localhost:8765');
    socket.binaryType = 'arraybuffer';
    setWs(socket);

    let prevUrl = null;

    socket.onmessage = async (e) => {
      if (e.data instanceof ArrayBuffer) {
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
      } else {
        const message = JSON.parse(e.data);
        setMappingItems(message.data);        
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
            {frame && <img className={styles.camera} src={frame} alt='realtime-video' />}
          </div>
        </div>
        <div className={styles.right}>
          <div className={styles.target_container}>
            <span className={styles.title}>표적지</span>
            <div className={styles.target}>
              <div className={styles.LT}>
                <input className={styles.target_input} type="number" name="LT_x" value={corner.LT.x} onChange={handleCornerCoordinate} />
                <input className={styles.target_input} type="number" name="LT_y" value={corner.LT.y} onChange={handleCornerCoordinate} />
              </div>
              <div className={styles.RT}>
                <input className={styles.target_input} type="number" name="RT_x" value={corner.RT.x} onChange={handleCornerCoordinate} />
                <input className={styles.target_input} type="number" name="RT_y" value={corner.RT.y} onChange={handleCornerCoordinate} />
              </div>
              <div className={styles.LB}>
                <input className={styles.target_input} type="number" name="LB_x" value={corner.LB.x} onChange={handleCornerCoordinate} />
                <input className={styles.target_input} type="number" name="LB_y" value={corner.LB.y} onChange={handleCornerCoordinate} />
              </div>
              <div className={styles.RB}>
                <input className={styles.target_input} type="number" name="RB_x" value={corner.RB.x} onChange={handleCornerCoordinate} />
                <input className={styles.target_input} type="number" name="RB_y" value={corner.RB.y} onChange={handleCornerCoordinate} />
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
                  <input className={styles.target_input} type="number" name="x" value={range.x} onChange={handleRange} />
                  <span>좌우:</span>
                  <input className={styles.target_input} type="number" name="y" value={range.y} onChange={handleRange} />
                </div>
                <div className={styles.unit}>
                  <span>단위:</span>
                  <input className={styles.target_input} type="number" value={unit} onChange={handleUnit}/>
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
          <div>
            <MappingPoints title="PLC" mappingItem={mappingItems.PLC} onMappingItems={handleMappingItems} />
            <MappingPoints title="Pixel" mappingItem={mappingItems.Pixel} onMappingItems={handleMappingItems}/>
          </div>
        </div>
        <div className={styles.control}>
          <button className={`${shootMode === 0 ? styles.off : styles.on}`} onClick={handleShootMode}>사격</button>
          <button className={`${laserMode === 0 ? styles.off : styles.on}`}>레이저</button>
          <button className={styles.control_button}>원점</button>
          <button className={styles.control_button}>캡처</button>
          <button className={styles.control_button}>테스트</button>
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
  'LB': { 'x': defaultCenter.x + defaultRange.x, 'y': defaultCenter.y - defaultRange.y  },
  'RB': { 'x': defaultCenter.x - defaultRange.x, 'y': defaultCenter.y - defaultRange.y  },
};
const defaultMappingItems = {
  'PLC': [[0, 0], [0, 0], [0, 0], [0, 0]],
  'Pixel': [[0, 0], [0, 0], [0, 0], [0, 0]]
}