'use client'

import React, { useRef, useEffect } from 'react';
import * as THREE from 'three';
import { Button } from './ui/button';

interface MoleculeViewerProps {
  pdbData: string;
}

const MoleculeViewer3D: React.FC<MoleculeViewerProps> = ({ pdbData }) => {
  const mountRef = useRef<HTMLDivElement>(null);
  const sceneRef = useRef<THREE.Scene | null>(null);
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null);

  useEffect(() => {
    if (!mountRef.current) return;

    // Scene setup
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(75, 1, 0.1, 1000);
    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(400, 400);
    mountRef.current.appendChild(renderer.domElement);

    sceneRef.current = scene;
    rendererRef.current = renderer;
    camera.position.z = 5;

    // Parse PDB stub and create atoms
    const atoms = pdbData.split('\n').filter(line => line.startsWith('ATOM'));
    atoms.forEach((atom) => {
      const match = atom.match(/^\w+\s+(\w)/);
      const elem = match ? match[1] : 'C';
      const x = parseFloat(atom.slice(30, 38));
      const y = parseFloat(atom.slice(38, 46));
      const z = parseFloat(atom.slice(46, 54));
      
      const geometry = new THREE.SphereGeometry(0.3, 16, 16);
      const material = new THREE.MeshLambertMaterial({ 
        color: elem === 'C' ? 0xcccccc : elem === 'O' ? 0xff0000 : 0x4169e1 
      });
      const sphere = new THREE.Mesh(geometry, material);
      sphere.position.set(x, y, z);
      scene.add(sphere);
    });

    // Lighting
    const light = new THREE.DirectionalLight(0xffffff, 1);
    light.position.set(1, 1, 1);
    scene.add(light);
    scene.add(new THREE.AmbientLight(0x404040));

    // Animation
    const animate = () => {
      requestAnimationFrame(animate);
      renderer.render(scene, camera);
    };
    animate();

    // Cleanup
    return () => {
      if (mountRef.current && renderer.domElement) {
        mountRef.current.removeChild(renderer.domElement);
      }
    };
  }, [pdbData]);

  const measureDistance = () => {
    alert('Measure tool: click two atoms');
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
      <div className="flex gap-2 mb-4">
        <Button variant="outline" size="sm" onClick={() => sceneRef.current?.rotateY(0.1)}>
          Rotate
        </Button>
        <Button variant="outline" size="sm" onClick={measureDistance}>
          Measure
        </Button>
      </div>
      <div ref={mountRef} className="w-full h-96 border rounded-lg bg-gradient-to-b from-gray-100 to-gray-200 dark:from-gray-700 dark:to-gray-800" />
    </div>
  );
};

export default MoleculeViewer3D;

