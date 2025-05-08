import React from 'react';
import styles from './MappingPoints.module.css'

export default function MappingPoints({title, mappingItem, onMappingItems}) {
    return (
        <div className={styles.mapping_container}>
            <span className={styles.title}>{title}</span>
            {
                mappingItem.map((coordinate, idx) => (
                    <div key={`${title}_${idx}`}>
                        <input className={styles.coordinate_input} type="number" name={`${title}_${idx}_0`} value={coordinate[0]} onChange={onMappingItems} />
                        <input className={styles.coordinate_input} type="number" name={`${title}_${idx}_1`} value={coordinate[1]} onChange={onMappingItems} />
                    </div>
                ))
            }
        </div>
    );
}

