import { useEffect, useRef } from "react";
import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";

export function Lattice({
  extents,
  separation,
  time,
  sourceT,
}: {
  extents: number[];
  separation: number;
  time: number;
  sourceT: number;
}) {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const container = ref.current!;
    let renderer: THREE.WebGLRenderer;
    try {
      renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    } catch {
      container.textContent =
        "WebGL is unavailable. Source geometry is described below.";
      return;
    }
    renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
    container.appendChild(renderer.domElement);
    renderer.domElement.setAttribute(
      "aria-label",
      "Rotatable spatial lattice geometry. Drag to rotate; scroll to zoom.",
    );
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(38, 1, 0.1, 300);
    const max = Math.max(...extents.slice(0, 3));
    camera.position.set(max * 1.6, max * 1.1, max * 1.8);
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.minDistance = max;
    controls.maxDistance = max * 8;
    const positions: number[] = [],
      nodes: number[] = [];
    // Large geometries are sampled for legibility; this is geometry, not a field configuration.
    const stride = max > 12 ? 2 : 1;
    const xyz = (x: number, y: number, z: number) => [
      x - (extents[0] - 1) / 2,
      y - (extents[1] - 1) / 2,
      z - (extents[2] - 1) / 2,
    ];
    for (let x = 0; x < extents[0]; x += stride)
      for (let y = 0; y < extents[1]; y += stride)
        for (let z = 0; z < extents[2]; z += stride) {
          const p = xyz(x, y, z);
          nodes.push(...p);
          [x, y, z].forEach((value, axis) => {
            if (value + stride < extents[axis]) {
              const q = [x, y, z];
              q[axis] += stride;
              positions.push(...p, ...xyz(...(q as [number, number, number])));
            }
          });
        }
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute(
      "position",
      new THREE.Float32BufferAttribute(positions, 3),
    );
    scene.add(
      new THREE.LineSegments(
        geometry,
        new THREE.LineBasicMaterial({
          color: 0x406575,
          transparent: true,
          opacity: 0.32,
        }),
      ),
    );
    const points = new THREE.BufferGeometry();
    points.setAttribute("position", new THREE.Float32BufferAttribute(nodes, 3));
    scene.add(
      new THREE.Points(
        points,
        new THREE.PointsMaterial({
          color: 0x7fa6b5,
          size: 0.045,
          transparent: true,
          opacity: 0.6,
        }),
      ),
    );
    const anchor = Math.floor((extents[0] - separation - 1) / 2);
    const a = new THREE.Vector3(
      ...xyz(anchor, Math.floor(extents[1] / 2), Math.floor(extents[2] / 2)),
    );
    const b = a.clone().add(new THREE.Vector3(separation, 0, 0));
    const active = time <= sourceT;
    [a, b].forEach((position, index) => {
      const sphere = new THREE.Mesh(
        new THREE.SphereGeometry(0.15, 24, 24),
        new THREE.MeshBasicMaterial({
          color: index ? 0xe7ac7d : 0x72d6c7,
          transparent: true,
          opacity: active ? 1 : 0.25,
        }),
      );
      sphere.position.copy(position);
      scene.add(sphere);
      const halo = new THREE.Mesh(
        new THREE.SphereGeometry(0.29, 24, 24),
        new THREE.MeshBasicMaterial({
          color: index ? 0xe7ac7d : 0x72d6c7,
          wireframe: true,
          transparent: true,
          opacity: active ? 0.3 : 0.1,
        }),
      );
      halo.position.copy(position);
      scene.add(halo);
    });
    const line = new THREE.BufferGeometry().setFromPoints([a, b]);
    scene.add(
      new THREE.Line(
        line,
        new THREE.LineDashedMaterial({
          color: 0xb8d7be,
          dashSize: 0.12,
          gapSize: 0.1,
          transparent: true,
          opacity: time === 0 || time === sourceT ? 0.9 : 0.2,
        }),
      ).computeLineDistances(),
    );
    scene.add(new THREE.AxesHelper(max * 0.35));
    const resize = () => {
      const w = container.clientWidth,
        h = container.clientHeight;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    };
    const observer = new ResizeObserver(resize);
    observer.observe(container);
    resize();
    let frame = 0;
    const render = () => {
      controls.update();
      renderer.render(scene, camera);
      frame = requestAnimationFrame(render);
    };
    render();
    return () => {
      cancelAnimationFrame(frame);
      observer.disconnect();
      controls.dispose();
      scene.traverse((object) => {
        if (
          object instanceof THREE.Mesh ||
          object instanceof THREE.Line ||
          object instanceof THREE.Points
        ) {
          object.geometry.dispose();
          const materials = Array.isArray(object.material)
            ? object.material
            : [object.material];
          materials.forEach((material) => material.dispose());
        }
      });
      renderer.dispose();
      container.replaceChildren();
    };
  }, [extents.join(","), separation, time, sourceT]);
  return <div className="lattice-canvas" ref={ref} />;
}
