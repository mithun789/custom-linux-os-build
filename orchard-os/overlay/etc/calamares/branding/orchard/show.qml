import QtQuick 2.0;
import calamares.slideshow 1.0;

Presentation {
    id: presentation

    function nextSlide() { presentation.goToNextSlide(); }

    Timer {
        id: advanceTimer
        interval: 9000
        running: presentation.activatedInCalamares
        repeat: true
        onTriggered: nextSlide()
    }

    Slide {
        Image { id: bg1; source: "slide1.png"; anchors.fill: parent; fillMode: Image.PreserveAspectCrop }
        Text {
            anchors.centerIn: parent
            color: "white"; font.pixelSize: 28; font.bold: true
            text: "Welcome to Orchard OS"
        }
        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.top: parent.verticalCenter; anchors.topMargin: 30
            color: "#D8E2EC"; font.pixelSize: 16
            text: "A calm desktop with a dock, Spotlight search and light/dark themes."
        }
    }
    Slide {
        Image { source: "slide1.png"; anchors.fill: parent; fillMode: Image.PreserveAspectCrop }
        Text {
            anchors.centerIn: parent; width: parent.width * 0.8
            horizontalAlignment: Text.AlignHCenter; wrapMode: Text.WordWrap
            color: "white"; font.pixelSize: 20
            text: "Get apps from the Software store, or enable Flathub in the Welcome window for thousands more."
        }
    }
    Slide {
        Image { source: "slide1.png"; anchors.fill: parent; fillMode: Image.PreserveAspectCrop }
        Text {
            anchors.centerIn: parent; width: parent.width * 0.8
            horizontalAlignment: Text.AlignHCenter; wrapMode: Text.WordWrap
            color: "white"; font.pixelSize: 20
            text: "Orchard AI runs language models privately on your computer. Open it from the dock after installing."
        }
    }

    function onActivate() { }
    function onLeave() { }
}
