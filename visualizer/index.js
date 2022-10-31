function addLine(group, points) {
    const lineWidth = 5
    const lineGeometry = new THREE.BufferGeometry()
    .setFromPoints( points )
    const lineMaterial = new THREE.LineBasicMaterial({
        color: 0x000000,
        linewidth: lineWidth,
    })
    const line = new THREE.Line( lineGeometry, lineMaterial )
    group.add( line )
}

function addContainer(group, container) {
    addLine(
        group,
        [
            new THREE.Vector3(0, 0, 0),
            new THREE.Vector3(container.depth, 0, 0),
            new THREE.Vector3(container.depth, container.height, 0),
            new THREE.Vector3(0, container.height, 0),
            new THREE.Vector3(0, 0, 0),
        ]
    )
    addLine(
        group,
        [
            new THREE.Vector3(0, 0, 0),
            new THREE.Vector3(0, container.height, 0),
            new THREE.Vector3(0, container.height, container.width),
            new THREE.Vector3(0, 0, container.width),
            new THREE.Vector3(0, 0, 0),
        ]
    )
    addLine(
        group,
        [
            new THREE.Vector3(container.depth, container.height, container.width),
            new THREE.Vector3(container.depth, container.height, 0),
            new THREE.Vector3(container.depth, 0, 0),
            new THREE.Vector3(container.depth, 0, container.width),
            new THREE.Vector3(container.depth, container.height, container.width),
        ]
    )
    addLine(
        group,
        [
            new THREE.Vector3(container.depth, container.height, container.width),
            new THREE.Vector3(container.depth, 0, container.width),
            new THREE.Vector3(0, 0, container.width),
            new THREE.Vector3(0, container.height, container.width),
            new THREE.Vector3(container.depth, container.height, container.width),
        ]
    )
}

function addBlock(group, block) {
    const { back, bottom, left, depth, height, width } = block
    const front = back + depth
    const top = bottom + height
    const right = left + width
    const blockObject = new THREE.Group()
    const cube = new THREE.Mesh(
        new THREE.BoxGeometry(depth, height, width),
        new THREE.MeshPhongMaterial({
            color: Math.floor(Math.random() * 256 * 256 * 256),
            opacity: 0.8,
            transparent: true,
        }),
    )
    cube.position.set(
        back + depth / 2,
        bottom + height / 2,
        left + width /  2,
    )
    blockObject.add( cube )
    if (!block.stackable) {
        const lineWidth = 5
        blockObject.add(
            new THREE.Line(
                new THREE.BufferGeometry().setFromPoints([
                    new THREE.Vector3(back, top, left),
                    new THREE.Vector3(front, top, right),
                ]),
                new THREE.LineBasicMaterial({
                    color: 0x000000,
                    linewidth: lineWidth,
                })
            )
        )
        blockObject.add(
            new THREE.Line(
                new THREE.BufferGeometry().setFromPoints([
                    new THREE.Vector3(back, top, right),
                    new THREE.Vector3(front, top, left),
                ]),
                new THREE.LineBasicMaterial({
                    color: 0x000000,
                    linewidth: lineWidth,
                })
            )
        )
    }
    group.add( blockObject )
}

function addPacking(group, packing) {
    addContainer(group, packing.container)
    packing.packed_blocks.forEach((block) => {
        addBlock(group, block)
    })
    const containerCenter = new THREE.Vector3(
        packing.container.depth / 2,
        packing.container.height / 2,
        packing.container.width / 2,
    )
    group.position.sub(containerCenter)
}

function generateGroups(packings) {
    const groups = packings.map((packing) => {
        const group = new THREE.Group()
        addPacking(group, packing)
        return group
    })
    return groups
}

function visualize(scene, group) {
    document.querySelectorAll("#packingCanvas").forEach((element) => {
        element.remove()
    })
    scene.clear()
    scene.background = new THREE.Color("white")
    const camera = new THREE.PerspectiveCamera(
        75, window.innerWidth / window.innerHeight
    )
    camera.position.set( 300, 0, 0 )

    const renderer = new THREE.WebGLRenderer()
    renderer.setSize( window.innerWidth, window.innerHeight )
    renderer.domElement.id = "packingCanvas"
    document.body.appendChild( renderer.domElement )

    scene.add(group)

    const directionalLight1 = new THREE.DirectionalLight(0xFFFFFF)
    directionalLight1.position.set( 400.0, 300.0, 200.0 )
    scene.add(directionalLight1)
    const directionalLight2 = new THREE.DirectionalLight(0xFFFFFF)
    directionalLight2.position.set( -100.0, -200.0, -300.0 )
    scene.add(directionalLight2)

    const controls = new THREE.OrbitControls(camera, renderer.domElement)
    controls.update()
    function animate() {
        requestAnimationFrame( animate )
        controls.update()
        renderer.render( scene, camera )
    }
    animate()
}

document.getElementById("import").onclick = function () {
    const files = document.getElementById("responseFiles").files
    if (files.length <= 0) {
        console.log("No Files Uploaded")
        return false
    }
    const file = files.item(0)
    const fr = new FileReader()
    const scene = new THREE.Scene()
    fr.onload = function (e) {
        document.querySelectorAll("#containerSelector").forEach((element) => {
            element.remove()
        })
        const result = JSON.parse(e.target.result)
        const groups = generateGroups(result.packings)
        const selectContainer = document.createElement("select")
        selectContainer.id = "containerSelector"
        result.packings.forEach((packing, index) => {
            if (packing.packed_blocks.length <= 0) return
            const option = document.createElement("option")
            option.value = index
            option.textContent = packing.container.name
            selectContainer.appendChild(option)
        })
        selectContainer.onchange = (event) => {
            const containerIndex = event.currentTarget.value
            visualize(scene, groups[containerIndex])
        }
        document.body.appendChild(selectContainer)
    }
    fr.readAsText(file)
}