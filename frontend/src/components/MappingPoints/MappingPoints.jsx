import React from 'react';
import styles from './MappingPoints.module.css'

export default function MappingPoints({title, mappingItem}) {
    return (
        <div className={styles.mapping_container}>
            <span className={styles.title}>{title}</span>
            {
                mappingItem.map((coordinate, idx) => (
                    <div key={`${title}_${idx}`}>
                        <input className={styles.coordinate_input} type="number" value={coordinate[0]} />
                        <input className={styles.coordinate_input} type="number" value={coordinate[1]} />
                    </div>
                ))
            }
        </div>
    );
}

